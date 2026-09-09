"""Compatibility entrypoint for the organized staging-data tool."""

from pesaguard_backend_pipeline.operations.seed_staging_data import *
from pesaguard_backend_pipeline.operations.seed_staging_data import seed_staging_data


if __name__ == "__main__":
    seed_staging_data()
