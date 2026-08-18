"""(b) Payout idempotency and (c) repeated simulation."""
from datetime import date

from app import models


def _payouts_for(db, policy_id):
    return (
        db.query(models.Payout)
        .join(models.Trigger)
        .filter(models.Trigger.policy_id == policy_id)
        .all()
    )


def test_double_click_produces_exactly_one_payout(client, db_session, drought_policy):
    """The headline guarantee: two identical calls, one payout."""
    policy_id = drought_policy["id"]
    first = client.post(f"/api/v1/simulate/drought/{policy_id}").json()
    second = client.post(f"/api/v1/simulate/drought/{policy_id}").json()

    assert first["triggered"] is True
    assert second["triggered"] is True
    assert first["idempotent_reuse"] is False
    assert second["idempotent_reuse"] is True
    assert first["trigger_id"] == second["trigger_id"]
    assert first["payout"]["payout_id"] == second["payout"]["payout_id"]
    assert len(_payouts_for(db_session, policy_id)) == 1


def test_ten_rapid_calls_still_one_payout(client, db_session, drought_policy):
    policy_id = drought_policy["id"]
    results = [client.post(f"/api/v1/simulate/drought/{policy_id}").json() for _ in range(10)]

    assert len({r["trigger_id"] for r in results}) == 1
    assert len({r["payout"]["payout_id"] for r in results}) == 1
    assert len(_payouts_for(db_session, policy_id)) == 1
    assert db_session.query(models.Trigger).filter_by(policy_id=policy_id).count() == 1


def test_repeated_simulation_is_deterministic(client, drought_policy):
    """(c) Same inputs, same outputs — every field, every time."""
    policy_id = drought_policy["id"]
    runs = [client.post(f"/api/v1/simulate/drought/{policy_id}").json() for _ in range(5)]

    for run in runs[1:]:
        assert run["observed_rainfall_mm"] == runs[0]["observed_rainfall_mm"]
        assert run["threshold_mm"] == runs[0]["threshold_mm"]
        assert run["triggered"] == runs[0]["triggered"]
        assert run["payout"]["amount"] == runs[0]["payout"]["amount"]
    assert runs[0]["payout"]["amount"] == "21600.00"


def test_different_dates_are_separate_evaluations(client, db_session, drought_policy):
    """Idempotency is per-date, not global — a new day is a new evaluation."""
    policy_id = drought_policy["id"]
    a = client.post(f"/api/v1/simulate/drought/{policy_id}?evaluation_date=2026-08-01").json()
    b = client.post(f"/api/v1/simulate/drought/{policy_id}?evaluation_date=2026-08-02").json()

    assert a["trigger_id"] != b["trigger_id"]
    assert len(_payouts_for(db_session, policy_id)) == 2


def test_non_triggering_evaluation_creates_no_payout(client, db_session, drought_policy):
    policy_id = drought_policy["id"]
    result = client.post(f"/api/v1/simulate/excess_rain/{policy_id}").json()

    # 150mm against a drought policy at 120mm: not a breach.
    assert result["triggered"] is False
    assert "payout" not in result
    assert _payouts_for(db_session, policy_id) == []


def test_database_constraint_blocks_duplicate_evaluation(db_session, drought_policy):
    """Belt and braces: even a direct insert cannot duplicate an evaluation."""
    import pytest
    from sqlalchemy.exc import IntegrityError

    policy_id = drought_policy["id"]
    common = dict(
        policy_id=policy_id, evaluation_date=date(2026, 8, 5),
        observed_value=11.0, threshold_value=120.0, triggered=1,
    )
    db_session.add(models.Trigger(**common))
    db_session.commit()
    db_session.add(models.Trigger(**common))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_database_constraint_blocks_duplicate_payout(db_session, drought_policy):
    import pytest
    from sqlalchemy.exc import IntegrityError
    from decimal import Decimal

    trigger = models.Trigger(
        policy_id=drought_policy["id"], evaluation_date=date(2026, 8, 6),
        observed_value=11.0, threshold_value=120.0, triggered=1,
    )
    db_session.add(trigger)
    db_session.commit()

    db_session.add(models.Payout(trigger_id=trigger.id, amount=Decimal("100.00")))
    db_session.commit()
    db_session.add(models.Payout(trigger_id=trigger.id, amount=Decimal("100.00")))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_reset_allows_a_repeat_rehearsal(client, db_session, drought_policy):
    policy_id = drought_policy["id"]
    client.post(f"/api/v1/simulate/drought/{policy_id}")
    assert len(_payouts_for(db_session, policy_id)) == 1

    reset = client.post(f"/api/v1/simulate/reset/{policy_id}").json()
    assert reset["payouts_deleted"] == 1
    assert _payouts_for(db_session, policy_id) == []

    again = client.post(f"/api/v1/simulate/drought/{policy_id}").json()
    assert again["idempotent_reuse"] is False
    assert len(_payouts_for(db_session, policy_id)) == 1


def test_reuse_repairs_a_trigger_left_without_a_payout(client, db_session, drought_policy):
    """A crash between the two commits must not strand a valid claim.

    The trigger and its payout commit separately. If the process dies in the
    gap, the evaluation exists and is triggered but has no payout — and every
    later call takes the reuse path. Without a repair the claim never pays.
    """
    policy_id = drought_policy["id"]
    eval_date = date(2026, 8, 11)

    # Exactly the state a crash in the gap leaves behind.
    db_session.add(
        models.Trigger(
            policy_id=policy_id, evaluation_date=eval_date,
            observed_value=11.0, threshold_value=120.0, triggered=1,
        )
    )
    db_session.commit()
    assert _payouts_for(db_session, policy_id) == []

    result = client.post(
        f"/api/v1/simulate/drought/{policy_id}?evaluation_date={eval_date.isoformat()}"
    ).json()

    assert result["triggered"] is True
    assert result["idempotent_reuse"] is True
    assert "payout" in result, "reuse returned a triggered evaluation with no payout"
    assert result["payout"]["amount"] == "21600.00"
    assert len(_payouts_for(db_session, policy_id)) == 1


def test_repairing_a_missing_payout_is_itself_idempotent(client, db_session, drought_policy):
    """Repair must not become a second way to create payouts."""
    policy_id = drought_policy["id"]
    eval_date = date(2026, 8, 13)
    db_session.add(
        models.Trigger(
            policy_id=policy_id, evaluation_date=eval_date,
            observed_value=11.0, threshold_value=120.0, triggered=1,
        )
    )
    db_session.commit()

    url = f"/api/v1/simulate/drought/{policy_id}?evaluation_date={eval_date.isoformat()}"
    results = [client.post(url).json() for _ in range(5)]

    assert len({r["payout"]["payout_id"] for r in results}) == 1
    assert len(_payouts_for(db_session, policy_id)) == 1


def test_repair_does_not_invent_a_payout_for_an_untriggered_evaluation(
    client, db_session, drought_policy
):
    """Only a breach pays. Repair must never manufacture a claim."""
    policy_id = drought_policy["id"]
    eval_date = date(2026, 8, 14)
    db_session.add(
        models.Trigger(
            policy_id=policy_id, evaluation_date=eval_date,
            observed_value=500.0, threshold_value=120.0, triggered=0,
        )
    )
    db_session.commit()

    result = client.post(
        f"/api/v1/simulate/drought/{policy_id}?evaluation_date={eval_date.isoformat()}"
    ).json()

    assert result["triggered"] is False
    assert "payout" not in result
    assert _payouts_for(db_session, policy_id) == []
