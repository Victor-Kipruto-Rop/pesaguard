import os
import sys

TESTS_DIR = os.path.dirname(__file__)
PACKAGE_DIR = os.path.dirname(TESTS_DIR)
REPOSITORY_ROOT = os.path.dirname(PACKAGE_DIR)

for path in (REPOSITORY_ROOT, PACKAGE_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-with-at-least-32-bytes")
