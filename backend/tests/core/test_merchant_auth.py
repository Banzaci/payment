from app.core.api_key import (
    generate_api_key,
    hash_api_key,
    verify_api_key,
)
from app.models.merchant import Merchant

def test_valid_merchant_api_key():
    api_key = generate_api_key()

    merchant = Merchant(
        name="Test Hotel",
        default_currency="GHS",
        api_key_hash=hash_api_key(api_key),
    )

    assert verify_api_key(
        api_key,
        merchant.api_key_hash,
    )


def test_invalid_merchant_api_key():
    api_key = generate_api_key()

    merchant = Merchant(
        name="Test Hotel",
        default_currency="GHS",
        api_key_hash=hash_api_key(api_key),
    )

    assert not verify_api_key(
        "invalid_key",
        merchant.api_key_hash,
    )
