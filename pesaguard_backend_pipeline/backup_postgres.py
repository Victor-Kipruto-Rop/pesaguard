#!/usr/bin/env python3
"""
Automated Postgres backup script with restoration testing.

Usage:
  python3 backup_postgres.py --help
  python3 backup_postgres.py --backup  # Create a backup
  python3 backup_postgres.py --restore /path/to/backup.sql  # Restore from backup

Deployment:
  1. Copy to /usr/local/bin/pesaguard-backup.py
  2. Copy systemd files to /etc/systemd/system/
  3. sudo systemctl daemon-reload && sudo systemctl enable --now pesaguard-backup.timer
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pesaguard:pesaguard@localhost:5432/pesaguard")
BACKUP_DIR = Path(os.getenv("PESAGUARD_BACKUP_DIR", "/var/backups/pesaguard"))
RETENTION_DAYS = int(os.getenv("PESAGUARD_BACKUP_RETENTION_DAYS", "30"))


def parse_db_url(url: str) -> dict:
    """Parse PostgreSQL URL into connection parameters."""
    # Format: postgresql://user:password@host:port/database
    if not url.startswith("postgresql://"):
        raise ValueError(f"Unsupported database URL scheme: {url}")
    
    url = url.replace("postgresql://", "")
    
    # Extract auth
    if "@" in url:
        auth, rest = url.split("@", 1)
        if ":" in auth:
            user, password = auth.split(":", 1)
        else:
            user = auth
            password = ""
    else:
        user = "postgres"
        password = ""
        rest = url
    
    # Extract host, port, database
    if "/" in rest:
        host_port, database = rest.split("/", 1)
    else:
        host_port = rest
        database = "postgres"
    
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host = host_port
        port = "5432"
    
    return {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "database": database,
    }


def create_backup() -> Path:
    """Create a timestamped backup of the Postgres database."""
    try:
        db_params = parse_db_url(DATABASE_URL)
    except Exception as e:
        logger.error(f"Failed to parse DATABASE_URL: {e}")
        sys.exit(1)
    
    # Ensure backup directory exists
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped backup file
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"pesaguard_{timestamp}.sql.gz"
    
    # Build pg_dump command with credentials
    env = os.environ.copy()
    if db_params["password"]:
        env["PGPASSWORD"] = db_params["password"]
    
    try:
        logger.info(f"Starting backup to {backup_file}")
        # Use pg_dump with gzip compression
        dump_cmd = [
            "pg_dump",
            "-h", db_params["host"],
            "-p", db_params["port"],
            "-U", db_params["user"],
            "-d", db_params["database"],
            "--no-password",
            "-F", "p",  # Plain text format (required for gzip)
        ]
        
        with open(backup_file, "w") as f:
            # Pipe through gzip for compression
            dump_process = subprocess.Popen(
                dump_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            
            gzip_process = subprocess.Popen(
                ["gzip", "-9"],
                stdin=dump_process.stdout,
                stdout=f,
                stderr=subprocess.PIPE,
            )
            
            dump_process.stdout.close()  # Allow dump_process to receive SIGPIPE
            _, err = gzip_process.communicate()
            
            if gzip_process.returncode != 0:
                raise subprocess.CalledProcessError(gzip_process.returncode, "gzip", stderr=err)
        
        # Verify backup file was created and contains data
        if not backup_file.exists() or backup_file.stat().st_size == 0:
            raise RuntimeError(f"Backup file is empty: {backup_file}")
        
        backup_size_mb = backup_file.stat().st_size / (1024 * 1024)
        logger.info(f"Backup created successfully: {backup_file} ({backup_size_mb:.2f} MB)")
        
        # Clean up old backups
        _cleanup_old_backups()
        
        return backup_file
    
    except subprocess.CalledProcessError as e:
        logger.error(f"pg_dump failed: {e.stderr.decode() if e.stderr else str(e)}")
        if backup_file.exists():
            backup_file.unlink()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        if backup_file.exists():
            backup_file.unlink()
        sys.exit(1)


def restore_backup(backup_file: Path) -> None:
    """Restore database from a backup file."""
    if not backup_file.exists():
        logger.error(f"Backup file not found: {backup_file}")
        sys.exit(1)
    
    try:
        db_params = parse_db_url(DATABASE_URL)
    except Exception as e:
        logger.error(f"Failed to parse DATABASE_URL: {e}")
        sys.exit(1)
    
    try:
        logger.info(f"Starting restoration from {backup_file}")
        
        env = os.environ.copy()
        if db_params["password"]:
            env["PGPASSWORD"] = db_params["password"]
        
        # Check if backup is gzipped
        is_gzipped = str(backup_file).endswith(".gz")
        
        if is_gzipped:
            # Decompress on the fly
            restore_cmd = [
                "psql",
                "-h", db_params["host"],
                "-p", db_params["port"],
                "-U", db_params["user"],
                "-d", db_params["database"],
                "--no-password",
                "-f", "-",  # Read from stdin
            ]
            
            with open(backup_file, "rb") as f:
                import gzip
                with gzip.open(f, "rt") as gz:
                    process = subprocess.Popen(
                        restore_cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        env=env,
                        text=True,
                    )
                    _, err = process.communicate(input=gz.read())
                    if process.returncode != 0:
                        raise subprocess.CalledProcessError(process.returncode, "psql", stderr=err)
        else:
            # Plain text restore
            restore_cmd = [
                "psql",
                "-h", db_params["host"],
                "-p", db_params["port"],
                "-U", db_params["user"],
                "-d", db_params["database"],
                "--no-password",
                "-f", str(backup_file),
            ]
            
            process = subprocess.run(restore_cmd, env=env, capture_output=True, text=True)
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "psql", stderr=process.stderr)
        
        logger.info(f"Restoration completed successfully from {backup_file}")
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Restoration failed: {e.stderr if e.stderr else str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Restoration failed: {e}")
        sys.exit(1)


def _cleanup_old_backups() -> None:
    """Remove backups older than RETENTION_DAYS."""
    from datetime import timedelta
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    
    for backup_file in sorted(BACKUP_DIR.glob("pesaguard_*.sql.gz")):
        try:
            # Extract timestamp from filename
            timestamp_str = backup_file.stem.replace("pesaguard_", "").replace(".sql", "")
            file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
            
            if file_time < cutoff:
                logger.info(f"Removing old backup: {backup_file}")
                backup_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to parse/clean backup {backup_file}: {e}")


def test_backup_integrity(backup_file: Path) -> bool:
    """Quick test: verify backup is valid SQL."""
    if not backup_file.exists():
        logger.warning(f"Backup file not found for integrity test: {backup_file}")
        return False
    
    try:
        import gzip
        if str(backup_file).endswith(".gz"):
            with gzip.open(backup_file, "rt") as f:
                content = f.read(1000)  # Read first 1000 chars
        else:
            with open(backup_file, "r") as f:
                content = f.read(1000)
        
        # Basic checks
        if not content or len(content.strip()) < 10:
            logger.warning(f"Backup file appears empty or corrupted: {backup_file}")
            return False
        
        if "CREATE" not in content and "INSERT" not in content:
            logger.warning(f"Backup file doesn't appear to contain SQL: {backup_file}")
            return False
        
        logger.info(f"Backup integrity check passed: {backup_file}")
        return True
    except Exception as e:
        logger.warning(f"Backup integrity check failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="PesaGuard PostgreSQL backup and restore utility")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--backup", action="store_true", help="Create a new backup")
    group.add_argument("--restore", type=str, metavar="BACKUP_FILE", help="Restore from backup file")
    group.add_argument("--test", action="store_true", help="Test backup integrity")
    group.add_argument("--list", action="store_true", help="List recent backups")
    
    args = parser.parse_args()
    
    if args.backup:
        backup_file = create_backup()
        if test_backup_integrity(backup_file):
            logger.info("Backup verification successful")
        else:
            logger.warning("Backup verification failed")
            sys.exit(1)
    
    elif args.restore:
        restore_backup(Path(args.restore))
    
    elif args.test:
        if not list(BACKUP_DIR.glob("pesaguard_*.sql.gz")):
            logger.warning(f"No backups found in {BACKUP_DIR}")
            sys.exit(1)
        
        latest_backup = sorted(BACKUP_DIR.glob("pesaguard_*.sql.gz"))[-1]
        if test_backup_integrity(latest_backup):
            logger.info("Latest backup integrity verified")
        else:
            sys.exit(1)
    
    elif args.list:
        backups = sorted(BACKUP_DIR.glob("pesaguard_*.sql.gz"), reverse=True)
        if not backups:
            logger.info(f"No backups found in {BACKUP_DIR}")
        else:
            logger.info(f"Recent backups in {BACKUP_DIR}:")
            for backup in backups[:10]:
                size_mb = backup.stat().st_size / (1024 * 1024)
                mtime = datetime.fromtimestamp(backup.stat().st_mtime)
                logger.info(f"  {backup.name} ({size_mb:.2f} MB) - {mtime}")


if __name__ == "__main__":
    main()
