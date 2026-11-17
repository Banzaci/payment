
import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


@pytest.fixture(autouse=True)
def mock_solana_mint(monkeypatch):
    monkeypatch.setenv(
        "SOLANA_USDC_MINT",
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    )


def test_default_settings(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    settings = Settings(_env_file=None)

    assert settings.app_name == "Payment Platform API"
    assert settings.debug is False
    assert settings.solana_rpc_url == "https://api.devnet.solana.com"


def test_environment_variables(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("ENVIRONMENT", "testing")

    settings = Settings(_env_file=None)

    assert settings.debug is True
    assert settings.environment == "testing"


def test_invalid_boolean(monkeypatch):
    monkeypatch.setenv("DEBUG", "invalid")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_cached():
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second
