
from uuid import uuid4

from app.models.payment import Payment


def test_payment_has_merchant_id():
    merchant_id = str(uuid4())

    payment = Payment(
        amount="200.00",
        currency="GHS",
        network="solana-devnet",
        recipient_address="test-address",
        reference="test-reference",
        payment_url="test-url",
        merchant_id=merchant_id,
    )

    assert payment.merchant_id == merchant_id
