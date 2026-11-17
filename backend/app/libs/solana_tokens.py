from decimal import Decimal

import httpx

from app.core.config import get_settings


async def get_token_balance(
    wallet: str,
    mint: str,
    client: httpx.AsyncClient | None = None,
) -> Decimal:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            wallet,
            {"mint": mint},
            {"encoding": "jsonParsed"},
        ],
    }

    async def fetch(http_client: httpx.AsyncClient) -> Decimal:
        response = await http_client.post(
            get_settings().solana_rpc_url,
            json=payload,
        )
        response.raise_for_status()

        data = response.json()

        if "error" in data:
            raise RuntimeError(f"Solana RPC error: {data['error']}")

        total = Decimal(0)

        for item in data["result"]["value"]:
            token_amount = item["account"]["data"]["parsed"]["info"][
                "tokenAmount"
            ]

            amount = Decimal(token_amount["amount"])
            decimals = int(token_amount["decimals"])

            total += amount / (Decimal(10) ** decimals)

        return total

    if client is not None:
        return await fetch(client)

    async with httpx.AsyncClient(timeout=10) as http_client:
        return await fetch(http_client)