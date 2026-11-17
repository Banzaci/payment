
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_payment_without_api_key():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/private/v1/payments",
            json={
                "amount": "10.50",
                "currency": "USDC",
                "network": "solana-devnet",
                "recipient_address": (
                    "7sceuy93FTMwt5QZCJ2aPJSvzNuV6T8euL183X1SYgAC"
                ),
            },
        )

    assert response.status_code == 401
