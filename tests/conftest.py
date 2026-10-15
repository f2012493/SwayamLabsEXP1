import pytest


@pytest.fixture(autouse=True)
def _isolated_run_log(tmp_path, monkeypatch):
    """Test moves must never mix with real evidence in runs/."""
    monkeypatch.setenv("SWAYAM_RUNS_DIR", str(tmp_path / "runs"))
