
from app.core.api_key import generate_api_key, hash_api_key, verify_api_key


def test_generate_api_key():
    api_key = generate_api_key()

    assert api_key.startswith("pk_")
    assert len(api_key) > 40


def test_hash_api_key():
    api_key = generate_api_key()
    hashed = hash_api_key(api_key)

    assert hashed != api_key
    assert len(hashed) == 64


def test_verify_api_key():
    api_key = generate_api_key()
    hashed = hash_api_key(api_key)

    assert verify_api_key(api_key, hashed) is True
    assert verify_api_key("invalid_key", hashed) is False
