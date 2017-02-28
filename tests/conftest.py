import os

import pytest


@pytest.fixture
def datadir(request):
    return os.path.join(os.path.dirname(request.module.__file__), 'data')
