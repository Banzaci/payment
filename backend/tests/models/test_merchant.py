
from app.models.merchant import Merchant
from app.core.api_key import generate_api_key, hash_api_key, verify_api_key

def test_create_merchant():
    merchant = Merchant(
        name="Test Restaurant",
        default_currency="GHS",
    )

    assert merchant.name == "Test Restaurant"
    assert merchant.default_currency == "GHS"
    assert merchant.id is None


def test_merchant_payment_methods():
    merchant = Merchant(
        name="Test Hotel",
        default_currency="GHS",
        enabled_payment_methods=["usdc", "card", "apple_pay"],
    )

    assert merchant.enabled_payment_methods == [
        "usdc",
        "card",
        "apple_pay",
    ]


def test_merchant_api_key():
    api_key = generate_api_key()

    merchant = Merchant(
        name="Test Hotel",
        default_currency="GHS",
        api_key_hash=hash_api_key(api_key),
    )

    assert merchant.api_key_hash != api_key
    assert verify_api_key(api_key, merchant.api_key_hash)
    assert not verify_api_key("invalid_key", merchant.api_key_hash)
