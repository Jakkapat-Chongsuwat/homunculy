"""
E2E test configuration.

This module imports fixtures from the unit test conftest for e2e testing.
"""

import pytest

# Import fixtures from unit test conftest
pytest_plugins = [
    "tests.unit.ai_agent.conftest",
]