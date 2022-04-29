import os
import pytest

BASE_PATH = os.path.dirname(__file__)


@pytest.hookimpl(tryfirst=True)
def pytest_load_initial_conftests(early_config, parser, args):
    os.environ["DATASET_ARCHIVE_ROOT"] = BASE_PATH