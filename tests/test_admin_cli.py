import json
import subprocess
import sys
import pathlib
import tempfile
import os

# Ensure repo root is on sys.path for imports in test env
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pesaguard_backend_pipeline.event_store import EventStore, ProcessResult


def _make_payload(trans_id: str):
    return {"TransID": trans_id, "TransAmount": "50", "MSISDN": "254700000001", "BusinessShortCode": "12345", "TransTime": "20220101120000"}


def test_admin_cli_outputs_processed(tmp_path):
    db_file = tmp_path / "admin.db"
    db_url = f"sqlite:///{db_file}"

    es = EventStore(database_url=db_url)
    payload = _make_payload("CLI_TEST_1")
    res = es.mark_processed(payload, tenant_id="test")
    assert res in {ProcessResult.STORED, ProcessResult.DUPLICATE}

    # run the CLI using the current python
    script = str(pathlib.Path(__file__).resolve().parents[1] / "scripts" / "admin_query.py")
    cmd = [sys.executable, script, "CLI_TEST_1", "--db", db_url]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(pathlib.Path(__file__).resolve().parents[1])
    out = subprocess.check_output(cmd, env=env)
    data = json.loads(out.decode("utf-8"))
    assert "CLI_TEST_1" in data
    assert data["CLI_TEST_1"] is not None
