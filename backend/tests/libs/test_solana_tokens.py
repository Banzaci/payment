import json
from decimal import Decimal

import httpx
import pytest

from app.libs.solana_tokens import get_token_balance


@pytest.mark.asyncio
async def test_get_token_balance():
    wallet = "11111111111111111111111111111111"
    mint = "So11111111111111111111111111111111111111112"

    def mock_rpc(request: httpx.Request):
        payload = json.loads(request.content)

        assert payload["method"] == "getTokenAccountsByOwner"
        assert payload["params"] == [
            wallet,
            {"mint": mint},
            {"encoding": "jsonParsed"},
        ]

        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "context": {"slot": 123},
                    "value": [
                        {
                            "account": {
                                "data": {
                                    "parsed": {
                                        "info": {
                                            "tokenAmount": {
                                                "amount": "12500000",
                                                "decimals": 6,
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    ],
                },
            },
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(mock_rpc),
    ) as client:
        balance = await get_token_balance(
            wallet,
            mint,
            client=client,
        )

    assert balance == Decimal("12.5")