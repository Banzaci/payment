from decimal import Decimal

import pytest

from app.libs.solana_rpc import get_sol_balance


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_balance_from_devnet():
    address = "11111111111111111111111111111111"

    balance = await get_sol_balance(address)

    assert isinstance(balance, Decimal)
    assert balance >= 0