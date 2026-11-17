import pytest

from app.libs.solana import is_valid_solana_address


@pytest.mark.parametrize(
    "address, expected",
    [
        ("11111111111111111111111111111111", True),
        ("", False),
        ("invalid-address", False),
        ("0x1234567890", False),
        ("1111111111111111111111111111111", False),
        ("111111111111111111111111111111111", False),
    ],
)
def test_solana_address_validation(address, expected):
    assert is_valid_solana_address(address) is expected