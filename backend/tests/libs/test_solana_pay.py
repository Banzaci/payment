from decimal import Decimal
from urllib.parse import urlparse, parse_qs

from app.libs.solana_pay import create_payment_url


def test_create_payment_url():
    recipient = "11111111111111111111111111111111"
    mint = "So11111111111111111111111111111111111111112"
    reference = "11111111111111111111111111111111"

    url = create_payment_url(
        recipient=recipient,
        amount=Decimal("10.50"),
        mint=mint,
        reference=reference,
    )

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    assert parsed.scheme == "solana"
    assert parsed.path == recipient
    assert params["amount"] == ["10.50"]
    assert params["spl-token"] == [mint]
    assert params["reference"] == [reference]