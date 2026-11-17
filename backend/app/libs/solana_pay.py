from decimal import Decimal
from urllib.parse import urlencode


def create_payment_url(
    recipient: str,
    amount: Decimal,
    mint: str,
    reference: str,
) -> str:
    if amount <= 0:
        raise ValueError("Amount must be positive")

    params = urlencode({
        "amount": str(amount),
        "spl-token": mint,
        "reference": reference,
    })

    return f"solana:{recipient}?{params}"