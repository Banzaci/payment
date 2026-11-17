import pytest
import httpx

from app.libs.solana_rpc import get_sol_balance


@pytest.mark.asyncio
async def test_get_sol_balance():
    def mock_rpc(request: httpx.Request):
        payload = __import__("json").loads(request.content)

        assert payload["method"] == "getBalance"
        assert payload["params"] == [
            "11111111111111111111111111111111"
        ]

        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "result": {
                    "context": {"slot": 123},
                    "value": 1500000000,
                },
            },
        )

    transport = httpx.MockTransport(mock_rpc)

    async with httpx.AsyncClient(transport=transport) as client:
        balance = await get_sol_balance(
            "11111111111111111111111111111111",
            client=client,
        )

    assert balance == 1.5