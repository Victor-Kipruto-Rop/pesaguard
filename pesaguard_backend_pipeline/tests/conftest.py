import os
import sys

ROOT = os.path.dirname(__file__)
PACKAGE_DIR = os.path.join(ROOT, "pesaguard_backend_pipeline")

if PACKAGE_DIR not in sys.path:
    sys.path.insert(0, PACKAGE_DIR)
