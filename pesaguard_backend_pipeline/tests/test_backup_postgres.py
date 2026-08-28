import gzip
import io
from pathlib import Path

import pytest

from pesaguard_backend_pipeline import backup_postgres


def test_parse_db_url_parses_postgresql_url():
    result = backup_postgres.parse_db_url("postgresql://user:pass@dbhost:5432/mydb")

    assert result == {
        "user": "user",
        "password": "pass",
        "host": "dbhost",
        "port": "5432",
        "database": "mydb",
    }


def test_parse_db_url_rejects_unsupported_scheme():
    with pytest.raises(ValueError):
        backup_postgres.parse_db_url("mysql://user:pass@dbhost:3306/mydb")


def test_backup_integrity_passes_for_valid_gzip(tmp_path):
    backup_file = tmp_path / "pesaguard_test.sql.gz"
    content = "PostgreSQL database dump\nCREATE TABLE foo (id int);\nINSERT INTO foo VALUES (1);\n"
    with gzip.open(backup_file, "wt", encoding="utf-8") as f:
        f.write(content)

    assert backup_postgres.test_backup_integrity(backup_file) is True


def test_backup_integrity_fails_for_corrupted_gzip(tmp_path):
    backup_file = tmp_path / "pesaguard_corrupt.sql.gz"
    backup_file.write_bytes(b"not a valid gzip stream")

    assert backup_postgres.test_backup_integrity(backup_file) is False


class DummyProcess:
    def __init__(self):
        self.stdin = io.StringIO()
        self.stdout = io.BytesIO()
        self.stderr = io.BytesIO()
        self.returncode = 0

    def communicate(self):
        return "", ""


class DummyPopen:
    def __init__(self, *args, **kwargs):
        self._process = DummyProcess()
        self.stdin = self._process.stdin
        self.stdout = self._process.stdout
        self.stderr = self._process.stderr
        self.returncode = 0

    def communicate(self):
        return self._process.communicate()


def test_restore_backup_streams_sql_file_to_psql(monkeypatch, tmp_path):
    backup_file = tmp_path / "pesaguard_test.sql.gz"
    content = "PostgreSQL database dump\nCREATE TABLE foo (id int);\n"
    with gzip.open(backup_file, "wt", encoding="utf-8") as f:
        f.write(content)

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/pesaguard")
    monkeypatch.setattr(backup_postgres.shutil, "which", lambda name: name)
    monkeypatch.setattr(backup_postgres.subprocess, "Popen", lambda *args, **kwargs: DummyPopen())

    backup_postgres.restore_backup(backup_file)
    assert backup_file.exists()


def test_create_backup_uses_pg_dump_and_writes_gzipped_file(monkeypatch, tmp_path):
    monkeypatch.setenv("PESAGUARD_BACKUP_DIR", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/pesaguard")
    monkeypatch.setenv("PGPASSWORD", "secret")
    monkeypatch.setattr(backup_postgres.shutil, "which", lambda name: name)

    dump_payload = b"PostgreSQL database dump\nCREATE TABLE foo (id int);\n"

    class FakePipe(io.BytesIO):
        def close(self):
            # Simulate pipe closure without invalidating content read by gzip
            try:
                self.seek(0)
            except Exception:
                pass

    class FakePopen:
        def __init__(self, args, stdout=None, stderr=None, env=None, stdin=None, text=False):
            self.args = args
            self.stderr = io.BytesIO()
            self.returncode = 0
            self.stdin = stdin
            command = args[0] if isinstance(args[0], str) else args[0][0]
            if command.endswith("pg_dump"):
                self.stdout = FakePipe(dump_payload)
            else:
                self.stdout = stdout

        def communicate(self):
            command = self.args[0] if isinstance(self.args[0], str) else self.args[0][0]
            if command.endswith("gzip"):
                data = self.stdin.read() if self.stdin is not None else b""
                import gzip as gzip_module
                compressed = gzip_module.compress(data)
                if hasattr(self.stdout, "write"):
                    self.stdout.write(compressed)
                return b"", b""
            return b"", b""

    def fake_popen(*args, **kwargs):
        return FakePopen(args[0], **kwargs)

    monkeypatch.setattr(backup_postgres.subprocess, "Popen", fake_popen)
    backup_file = backup_postgres.create_backup()

    assert backup_file.exists()
    assert backup_file.suffix == ".gz"

    with gzip.open(backup_file, "rt", encoding="utf-8") as f:
        restored = f.read()
    assert "CREATE TABLE foo" in restored


def test_get_database_url_uses_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host:5432/db")
    assert backup_postgres.get_database_url() == "postgresql://user:pass@host:5432/db"


def test_get_backup_dir_uses_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("PESAGUARD_BACKUP_DIR", str(tmp_path))
    assert backup_postgres.get_backup_dir() == tmp_path


def test_get_retention_days_defaults(monkeypatch):
    monkeypatch.delenv("PESAGUARD_BACKUP_RETENTION_DAYS", raising=False)
    assert backup_postgres.get_retention_days() == 30


def test_get_retention_days_overrides(monkeypatch):
    monkeypatch.setenv("PESAGUARD_BACKUP_RETENTION_DAYS", "60")
    assert backup_postgres.get_retention_days() == 60


def test_cleanup_old_backups_prunes_expired_files(tmp_path, monkeypatch):
    monkeypatch.setenv("PESAGUARD_BACKUP_DIR", str(tmp_path))
    old_file = tmp_path / "pesaguard_20000101_000000.sql.gz"
    new_file = tmp_path / "pesaguard_20990101_000000.sql.gz"
    old_file.write_bytes(b"dummy")
    new_file.write_bytes(b"dummy")

    monkeypatch.setenv("PESAGUARD_BACKUP_RETENTION_DAYS", "30")
    backup_postgres._cleanup_old_backups()

    assert not old_file.exists()
    assert new_file.exists()


def test_get_backup_dir_falls_back_to_writable_directory(tmp_path, monkeypatch):
    monkeypatch.delenv("PESAGUARD_BACKUP_DIR", raising=False)
    monkeypatch.setattr(backup_postgres, "BACKUP_DIR", tmp_path / "default")

    fallback_dir = backup_postgres.get_backup_dir()

    assert fallback_dir == backup_postgres._first_writable_dir([tmp_path / "default", tmp_path / "tmp", tmp_path / "cwd"])
