"""Architectural fitness: AI can never authorise a payout.

This walks the import graph of the modules that decide and create money. If
anyone imports a model, an LLM client, or a network library into that path, the
build fails here rather than in production.

This is the one test that must never be skipped or marked xfail.
"""
import ast
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"

# Modules on the money path.
MONEY_PATH_MODULES = [
    APP_DIR / "services" / "trigger_engine.py",
    APP_DIR / "services" / "payout_engine.py",
]

FORBIDDEN_PREFIXES = (
    "anthropic", "openai", "sklearn", "lightgbm", "xgboost", "torch",
    "tensorflow", "transformers", "requests", "httpx", "urllib", "socket",
    "app.services.explain", "app.services.risk", "app.services.weather",
)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def test_money_path_imports_nothing_forbidden():
    violations = []
    for module in MONEY_PATH_MODULES:
        for imported in _imports(module):
            for prefix in FORBIDDEN_PREFIXES:
                if imported == prefix or imported.startswith(prefix + "."):
                    violations.append(f"{module.name} imports {imported}")
    assert not violations, (
        "AI, network or data-access imports found on the money path: "
        + "; ".join(violations)
    )


def test_trigger_engine_is_pure_stdlib():
    """The trigger engine decides breaches. It must depend on nothing at all."""
    assert _imports(APP_DIR / "services" / "trigger_engine.py") == set()


def test_trigger_engine_runs_without_the_application():
    """Delete the rest of the app and this must still evaluate correctly."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "isolated_trigger_engine", APP_DIR / "services" / "trigger_engine.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.evaluate_trigger("drought", 82.4, 120.0) is True
    assert module.evaluate_trigger("drought", 150.0, 120.0) is False


def test_no_endpoint_creates_a_payout_directly():
    """Payouts originate only in the evaluation service, so every rupee traces
    to a stored evaluation."""
    offenders = []
    for path in (APP_DIR / "api").rglob("*.py"):
        if "models.Payout(" in path.read_text():
            offenders.append(path.name)
    assert not offenders, f"API modules constructing Payout directly: {offenders}"


# ---------------------------------------------------------------------------
# Risk engine isolation: risk estimates, it never settles.
# ---------------------------------------------------------------------------

RISK_DIR = APP_DIR / "services" / "risk"

# The risk engine may read the weather cache and call the trigger engine. It may
# never reach anything that authorises or records money.
RISK_FORBIDDEN_IMPORTS = (
    "app.services.payout_engine",
    "app.services.evaluation",
    "anthropic", "openai",
    # Tier-2/Tier-3 methods are out of scope for Tier-1 and must stay out until
    # they are deliberately introduced.
    "sklearn", "lightgbm", "xgboost", "torch", "tensorflow", "statsmodels",
    "requests", "httpx", "urllib",
)

# The pure layer must additionally stay free of the database.
RISK_PURE_MODULES = (
    RISK_DIR / "burn_analysis.py",
    RISK_DIR / "classification.py",
)


def test_risk_engine_cannot_reach_payout_or_settlement():
    violations = []
    for path in RISK_DIR.rglob("*.py"):
        for imported in _imports(path):
            for prefix in RISK_FORBIDDEN_IMPORTS:
                if imported == prefix or imported.startswith(prefix + "."):
                    violations.append(f"{path.name} imports {imported}")
    assert not violations, (
        "risk engine reaches settlement, ML or network code: " + "; ".join(violations)
    )


def test_risk_engine_never_constructs_a_payout_or_trigger():
    """Only the evaluation service may create these rows."""
    offenders = []
    for path in RISK_DIR.rglob("*.py"):
        text = path.read_text()
        for forbidden in ("models.Payout(", "models.Trigger("):
            if forbidden in text:
                offenders.append(f"{path.name}: {forbidden}")
    assert not offenders, f"risk modules constructing settlement rows: {offenders}"


def test_risk_api_exposes_no_write_endpoint():
    """Risk endpoints POST for convenience, but must not persist anything."""
    text = (APP_DIR / "api" / "v1" / "risk.py").read_text()
    for forbidden in ("db.add(", "db.commit(", "db.delete(", "models.Payout(", "models.Trigger("):
        assert forbidden not in text, f"risk router performs a write: {forbidden}"


def test_risk_pure_layer_has_no_database_dependency():
    """burn_analysis and classification must run without a database."""
    forbidden = ("sqlalchemy", "app.models", "app.core.database", "app.services.weather")
    violations = []
    for path in RISK_PURE_MODULES:
        for imported in _imports(path):
            for prefix in forbidden:
                if imported == prefix or imported.startswith(prefix + "."):
                    violations.append(f"{path.name} imports {imported}")
    assert not violations, f"pure risk layer touches the database: {violations}"


def test_burn_analysis_reuses_the_trigger_engine():
    """There must be exactly one definition of drought/excess-rain."""
    text = (RISK_DIR / "burn_analysis.py").read_text()
    assert "trigger_engine" in _imports(RISK_DIR / "burn_analysis.py") or any(
        i.endswith("trigger_engine") or i == "app.services" for i in _imports(RISK_DIR / "burn_analysis.py")
    ), "burn analysis must import the trigger engine"
    assert "trigger_engine.evaluate_trigger(" in text, (
        "burn analysis must call trigger_engine.evaluate_trigger rather than "
        "restating the comparison"
    )
    # Guard against a second, drifting definition of the comparison.
    assert "< threshold" not in text and "> threshold" not in text, (
        "burn analysis appears to reimplement the threshold comparison"
    )
