"""Suite-wide isolation: restore os.environ after every test.

Some production entry points set process env on purpose
(e.g. laya_worker.load_engine forces HF_HUB_OFFLINE before importing
laya, adapter_expand pins HF offline at import). Under pytest all tests
share one process, so those flags leaked into later tests and turned
unrelated network-touching tests red (observed: test_openui_runtime
benchmarks failing with OfflineModeIsEnabled after test_laya_worker).
Snapshotting environ per test keeps production behavior intact while
making the suite order-independent."""
import os

import pytest


@pytest.fixture(autouse=True)
def _restore_environ():
    env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(env)
