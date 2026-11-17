import secrets

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def is_valid_solana_address(address: str) -> bool:
    if not isinstance(address, str) or not address:
        return False

    number = 0

    for char in address:
        if char not in BASE58_ALPHABET:
            return False

        number = number * 58 + BASE58_ALPHABET.index(char)

    leading_zeros = len(address) - len(address.lstrip("1"))

    decoded = (
        b"\x00" * leading_zeros
        + (number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b"")
    )

    return len(decoded) == 32


def generate_solana_reference() -> str:
    alphabet = BASE58_ALPHABET
    data = secrets.token_bytes(32)

    number = int.from_bytes(data, "big")
    encoded = ""

    while number:
        number, remainder = divmod(number, 58)
        encoded = alphabet[remainder] + encoded

    return "1" * (len(data) - len(data.lstrip(b"\x00"))) + encoded