"""Every pipeline script parses and imports (no network at import time)."""
import ast, glob, importlib, os
import pytest

AUTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = sorted(glob.glob(os.path.join(AUTO, "pipeline", "*.py"))) + [os.path.join(AUTO, "newsletter", "draft.py")]


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: os.path.relpath(p, AUTO))
def test_parses(path):
    ast.parse(open(path, encoding="utf-8").read(), filename=path)


@pytest.mark.parametrize("path", [p for p in SCRIPTS if "pipeline" in p], ids=lambda p: os.path.basename(p))
def test_imports(path):
    importlib.import_module(os.path.splitext(os.path.basename(path))[0])


def test_newsletter_draft_imports():
    import importlib.util
    spec = importlib.util.spec_from_file_location("draft", SCRIPTS[-1])
    spec.loader.exec_module(importlib.util.module_from_spec(spec))
