"""pycln `__init__.py`/`pyproject.toml` metadata tests."""
import warnings

import pytest
import requests
import toml
from semver import VersionInfo
from typer import Exit

from pycln import PYPROJECT_PATH, __doc__, __name__, __version__, version_callback

from .utils import sysu

# Constants.
PYCLN_METADATA = toml.load(PYPROJECT_PATH)["tool"]["poetry"]
PYCLN_PYPI_URL = f"https://pypi.org/pypi/{__name__}/json"


class TestMetadata:

    """`__init__.py`/`pyproject.toml` test case."""

    def test_pyproject_path(self):
        assert PYPROJECT_PATH.is_file()
        assert str(PYPROJECT_PATH).endswith("pyproject.toml")

    def test_doc(self):
        assert type(__doc__) is str
        assert len(__doc__) > 30, "Too short description!"
        assert len(__doc__) <= 100, "Too long description!"
        assert __doc__ == PYCLN_METADATA["description"]

    def test_name(self):
        assert type(__name__) is str
        assert __name__ == PYCLN_METADATA["name"] == "pycln"

    def test_validate_semver(self):
        # It follows strictly the 2.0.0 version of the SemVer scheme.
        # For more information: https://semver.org/spec/v2.0.0.html
        assert type(__version__) is str
        assert VersionInfo.isvalid(__version__), (
            "Invalid semantic-version."
            "For more information: https://semver.org/spec/v2.0.0.html"
        )
        assert __version__ == PYCLN_METADATA["version"]

    @pytest.mark.skipif(
        not VersionInfo.isvalid(__version__), reason="Invalid semantic-version."
    )
    def test_compare_semver(self):
        # It follows strictly the 2.0.0 version of the SemVer scheme.
        # For more information: https://semver.org/spec/v2.0.0.html
        try:
            pycln_json = requests.get(PYCLN_PYPI_URL, timeout=2)
            latest_version = pycln_json.json()["info"]["version"]
            current_version = VersionInfo.parse(__version__)
            assert current_version.compare(latest_version) > -1, (
                "Current version can't be less than the "
                "latest released (https://pypi.org/project/pycln/) version!"
                "For more information: https://semver.org/spec/v2.0.0.html"
            )
        except (requests.ConnectionError, requests.Timeout):
            warnings.warn(
                UserWarning(
                    "Cannot validate the sequentiality of the current "
                    "semantic version; do to slow or no Internet access."
                )
            )

    @pytest.mark.parametrize(
        "value, expec_err, expec_exit_code",
        [
            pytest.param(True, Exit, 0, id="value=True"),
            pytest.param(False, None, None, id="value=False"),
        ],
    )
    def test_version_callback(self, value, expec_err, expec_exit_code):
        err_type, exit_code = None, None
        with sysu.std_redirect(sysu.STD.OUT) as stream:
            try:
                version_callback(value)
            except Exit as err:
                assert __version__ in str(stream.getvalue())
                err_type = Exit
                exit_code = err.exit_code
        assert err_type == expec_err
        assert exit_code == expec_exit_code