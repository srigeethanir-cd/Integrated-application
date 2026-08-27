"""Stub for pytest_mock package used in tests.
Provides a minimal MockerFixture class that proxies to unittest.mock.patch.
"""

from unittest.mock import patch

class MockerFixture:
    """Simple stub mimicking pytest_mock's MockerFixture.
    Allows `mocker.patch` calls in tests.
    """
    def __init__(self):
        self._patch = patch

    def patch(self, target, **kwargs):
        """Return a patch object for the given target.
        Mirrors the API of the real `mocker.patch`.
        """
        return self._patch(target, **kwargs)
