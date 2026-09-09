"""Compatibility entrypoint for the organized backup tool."""

from pesaguard_backend_pipeline.operations.backup_postgres import *
from pesaguard_backend_pipeline.operations.backup_postgres import main


if __name__ == "__main__":
    main()
