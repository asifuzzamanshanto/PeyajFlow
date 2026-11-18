import pytest

from app.credentials import generate_otp_code


@pytest.mark.parametrize("environment", ["development", "test"])
def test_otp_is_fixed_in_nonproduction_environments(monkeypatch, environment):
    monkeypatch.setenv("APP_ENV", environment)
    assert generate_otp_code() == "000000"


@pytest.mark.parametrize("environment", ["production", None])
def test_otp_is_random_outside_nonproduction_environments(
    monkeypatch, environment
):
    if environment is None:
        monkeypatch.delenv("APP_ENV", raising=False)
    else:
        monkeypatch.setenv("APP_ENV", environment)
    monkeypatch.setattr("app.credentials.secrets.randbelow", lambda _: 123456)
    assert generate_otp_code() == "123456"
