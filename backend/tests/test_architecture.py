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
