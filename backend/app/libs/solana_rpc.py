from decimal import Decimal
import httpx
from app.core.config import get_settings

async def get_signatures_for_address(
    address: str,
    limit: int = 20,
) -> list[dict]:
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            get_settings().solana_rpc_url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [
                    address,
                    {
                        "limit": limit,
                        "commitment": "finalized",
                    },
                ],
            },
        )

        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(data["error"])

        return data["result"]


async def get_transaction(
    signature: str,
) -> dict | None:
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            get_settings().solana_rpc_url,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    signature,
                    {
                        "encoding": "jsonParsed",
                        "commitment": "finalized",
                        "maxSupportedTransactionVersion": 0,
                    },
                ],
            },
        )

        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(data["error"])

        return data["result"]


async def get_sol_balance(
    address: str,
    client: httpx.AsyncClient | None = None,
) -> Decimal:
    settings = get_settings()

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [address],
    }

    async def request_balance(http_client: httpx.AsyncClient):
        response = await http_client.post(
            settings.solana_rpc_url,
            json=payload,
        )
        response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise RuntimeError(f"Solana RPC error: {data['error']}")

        return Decimal(data["result"]["value"]) / Decimal(1_000_000_000)

    if client is not None:
        return await request_balance(client)

    async with httpx.AsyncClient(timeout=10) as http_client:
        return await request_balance(http_client)