from importlib.metadata import version

import qyro


def test_public_version_matches_distribution_metadata():
    assert qyro.__version__ == version("qyro-engine")
