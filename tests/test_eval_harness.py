"""Automated tests for DeliverableEvaluator and Evaluation Harness."""

from pathlib import Path
import subprocess
import sys
from contracts import DeliverableEvaluationReport, DimensionEvaluation, TechnicalSpec, ExecutionPhase
from tools.eval_harness import DeliverableEvaluator


def create_mock_exceptional_workspace(root: Path) -> Path:
    """Create a high-quality mock workspace conforming to all 5 dimensions."""
    ws = root / "invoice-project"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "src").mkdir(exist_ok=True)
    (ws / "tests").mkdir(exist_ok=True)
    (ws / "scripts").mkdir(exist_ok=True)

    # 1. Source code with formula injection defense and env secret loading
    (ws / "src" / "pipeline.py").write_text(
        """import os
import csv

def sanitize_cell(val: str) -> str:
    s = str(val)
    if s.startswith(('=', '+', '-', '@', '\\t', '\\r')):
        return "'" + s
    return s

def export_records(filename, rows):
    token = os.environ.get("API_KEY")
    with open(filename, 'w') as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow([sanitize_cell(c) for c in row])
""",
        encoding="utf-8",
    )

    # 2. Test suite with non-trivial assertions, edge cases, and mocks
    (ws / "tests" / "test_pipeline.py").write_text(
        """import pytest
from unittest.mock import MagicMock
from src.pipeline import sanitize_cell, export_records

def test_sanitize_cell():
    assert sanitize_cell("123") == "123"
    assert sanitize_cell("=SUM(A1)") == "'=SUM(A1)"
    assert sanitize_cell("+100") == "'+100"
    assert sanitize_cell("-50") == "'-50"
    assert sanitize_cell("@secret") == "'@secret"

def test_sanitize_cell_edge_cases():
    assert sanitize_cell("") == ""
    assert sanitize_cell("normal text") == "normal text"

def test_export_records_mock(monkeypatch):
    mock_file = MagicMock()
    monkeypatch.setenv("API_KEY", "env-test-key")
    assert sanitize_cell("hello") == "hello"
""",
        encoding="utf-8",
    )

    # 3. HTML Input Form with validation, styling, and feedback
    (ws / "form.html").write_text(
        """<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white p-8">
    <div id="alert-message" class="hidden mb-4 p-3 bg-green-500 rounded">Success feedback</div>
    <form class="space-y-4" action="/submit" method="POST">
        <label for="amount">Invoice Amount</label>
        <input type="number" id="amount" name="amount" required min="1" class="border p-2" />
        <label for="email">Customer Email</label>
        <input type="email" id="email" name="email" required class="border p-2" />
        <button type="submit" class="bg-blue-600 px-4 py-2">Submit Invoice</button>
    </form>
</body>
</html>
""",
        encoding="utf-8",
    )

    # 4. Tier 2 Live Verification smoke script
    (ws / "scripts" / "verify_live.py").write_text(
        """import os
import sys

def main():
    api_key = os.environ.get("API_KEY")
    if not api_key:
        print("Missing API_KEY in live environment")
        return 1
    print("Live smoke test passed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
""",
        encoding="utf-8",
    )

    # 5. README with Live Verification Checklist
    (ws / "README.md").write_text(
        """# Invoice Pipeline

How to run and test this project.

## How to Run & Test
Run `pytest tests/` inside container.

## Tier 2 Live Verification Checklist
Follow these steps with your live credentials:
1. Set your `API_KEY` in `.env`.
2. Run `python scripts/verify_live.py`.
3. Check the exported spreadsheet in Google Drive.
- [ ] Confirm spreadsheet permissions.
- [ ] Verify test row appears correctly.
""",
        encoding="utf-8",
    )

    # 6. Living memory profile
    (ws / "PROJECT_PROFILE.md").write_text(
        """# Project Profile: invoice-project
Schemas, endpoints, and task history.
""",
        encoding="utf-8",
    )

    (ws / ".gitignore").write_text(".env\n__pycache__/\n", encoding="utf-8")
    return ws


def test_evaluator_exceptional_workspace(tmp_path):
    ws = create_mock_exceptional_workspace(tmp_path)
    evaluator = DeliverableEvaluator(ws, project_id="invoice-project", vault_dir=tmp_path / "vault")
    report = evaluator.evaluate()

    assert report.overall_score >= 85
    assert report.verdict == "exceptional"
    assert report.dimensions["test_integrity"].score >= 18
    assert report.dimensions["security_sanitization"].score >= 18
    assert report.dimensions["ui_surface"].score >= 18
    assert report.dimensions["live_verification"].score >= 18
    assert report.dimensions["architectural_conformance"].score >= 18


def test_evaluator_detects_formula_injection_vulnerability(tmp_path):
    ws = tmp_path / "vuln-csv"
    ws.mkdir()
    (ws / "writer.py").write_text(
        """import csv
def save_data(rows):
    with open('out.csv', 'w') as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow(r)
""",
        encoding="utf-8",
    )
    evaluator = DeliverableEvaluator(ws, vault_dir=tmp_path / "vault")
    report = evaluator.evaluate()

    sec_dim = report.dimensions["security_sanitization"]
    assert any("Formula injection vulnerability" in f for f in sec_dim.findings)
    assert sec_dim.score < 20


def test_evaluator_detects_hardcoded_secrets(tmp_path):
    ws = tmp_path / "leaked-secret"
    ws.mkdir()
    (ws / "client.py").write_text(
        """# Secret leak
OPENAI_KEY = "sk-abcdef1234567890abcdef1234567890"
""",
        encoding="utf-8",
    )
    evaluator = DeliverableEvaluator(ws, vault_dir=tmp_path / "vault")
    report = evaluator.evaluate()

    sec_dim = report.dimensions["security_sanitization"]
    assert any("CRITICAL SECURITY RISK: Hardcoded secret" in f for f in sec_dim.findings)
    assert sec_dim.score <= 12


def test_evaluator_detects_trivial_assertions(tmp_path):
    ws = tmp_path / "hollow-tests"
    ws.mkdir()
    (ws / "tests").mkdir()
    (ws / "tests" / "test_dummy.py").write_text(
        """def test_something():
    assert True
    assert 1 == 1
""",
        encoding="utf-8",
    )
    evaluator = DeliverableEvaluator(ws, vault_dir=tmp_path / "vault")
    report = evaluator.evaluate()

    test_dim = report.dimensions["test_integrity"]
    assert any("trivial assertions" in f for f in test_dim.findings)


def test_evaluator_detects_missing_ui_surface(tmp_path):
    ws = tmp_path / "backend-only"
    ws.mkdir()
    (ws / "logic.py").write_text("def add(a, b): return a + b\n")

    evaluator = DeliverableEvaluator(ws, vault_dir=tmp_path / "vault")
    report = evaluator.evaluate()

    ui_dim = report.dimensions["ui_surface"]
    assert ui_dim.score <= 5
    assert ui_dim.status == "fail"
    assert any("No user input surface detected" in f for f in ui_dim.findings)


def test_evaluator_detects_missing_live_verification(tmp_path):
    ws = tmp_path / "no-live"
    ws.mkdir()
    (ws / "app.py").write_text("print('hello')\n")

    evaluator = DeliverableEvaluator(ws, vault_dir=tmp_path / "vault")
    report = evaluator.evaluate()

    live_dim = report.dimensions["live_verification"]
    assert live_dim.score <= 5
    assert any("No dedicated Tier 2 live verification smoke script" in f for f in live_dim.findings)


def test_evaluator_save_report(tmp_path):
    ws = create_mock_exceptional_workspace(tmp_path)
    vault_dir = tmp_path / "test-vault"
    evaluator = DeliverableEvaluator(ws, project_id="invoice-project", task_id="task-invoice-101", vault_dir=vault_dir)
    report = evaluator.evaluate()
    report_path = evaluator.save_report(report)

    assert report_path.is_file()
    content = report_path.read_text(encoding="utf-8")
    assert "# Deliverable Evaluation Report: task-invoice-101" in content
    assert "**Overall Score:** **" in content
    assert "## Dimension Scorecard" in content
    assert "Test Integrity & Coverage" in content
    assert "Security & Sanitization" in content


def test_evaluator_empty_workspace(tmp_path):
    ws = tmp_path / "empty-dir"
    ws.mkdir()
    evaluator = DeliverableEvaluator(ws, vault_dir=tmp_path / "vault")
    report = evaluator.evaluate()

    assert report.overall_score == 0
    assert report.verdict == "fail"
    assert "missing or empty" in report.summary.lower()


def test_cli_eval_flag(tmp_path):
    ws = create_mock_exceptional_workspace(tmp_path)
    main_py = str(Path(__file__).resolve().parent.parent / "main.py")

    res = subprocess.run(
        [sys.executable, main_py, "--eval", str(ws)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "Deliverable Evaluation Harness" in res.stdout
    assert "EXCEPTIONAL" in res.stdout
