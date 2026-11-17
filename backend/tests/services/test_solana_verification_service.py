
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.services import solana_verification_service as service


REFERENCE = "test-reference"
RECIPIENT = "recipient-wallet"
MINT = "test-token-mint"
DESTINATION = "recipient-token-account"
SIGNATURE = "test-signature"


def make_transaction(
    *,
    recipient=RECIPIENT,
    mint=MINT,
    amount="10.50",
    destination=DESTINATION,
    received="10.50",
    error=None,
):
    decimals = 6
    initial_balance = 100_000_000
    received_raw = int(Decimal(received) * 10**decimals)

    return {
        "meta": {
            "err": error,
            "preTokenBalances": [
                {
                    "accountIndex": 1,
                    "mint": mint,
                    "owner": recipient,
                    "uiTokenAmount": {
                        "amount": str(initial_balance),
                        "decimals": decimals,
                    },
                }
            ],
            "postTokenBalances": [
                {
                    "accountIndex": 1,
                    "mint": mint,
                    "owner": recipient,
                    "uiTokenAmount": {
                        "amount": str(
                            initial_balance + received_raw
                        ),
                        "decimals": decimals,
                    },
                }
            ],
        },
        "transaction": {
            "message": {
                "accountKeys": [
                    {"pubkey": "sender"},
                    {"pubkey": destination},
                ],
                "instructions": [
                    {
                        "parsed": {
                            "type": "transferChecked",
                            "info": {
                                "mint": mint,
                                "destination": destination,
                                "tokenAmount": {
                                    "uiAmountString": amount,
                                },
                            },
                        },
                    }
                ],
            }
        },
    }


@pytest.mark.asyncio
async def test_incorrect_received_amount(mock_rpc):
    mock_rpc[1].return_value = make_transaction(
        amount="10.50",
        received="9.50",
    )

    result = await service.verify_solana_payment(
        REFERENCE,
        RECIPIENT,
        MINT,
        Decimal("10.50"),
    )

    assert result is None


@pytest.fixture
def mock_rpc(monkeypatch):
    signatures = AsyncMock(
        return_value=[
            {"signature": SIGNATURE, "err": None}
        ]
    )
    transaction = AsyncMock(
        return_value=make_transaction()
    )

    monkeypatch.setattr(
        service,
        "get_signatures_for_address",
        signatures,
    )
    monkeypatch.setattr(
        service,
        "get_transaction",
        transaction,
    )

    return signatures, transaction


@pytest.mark.asyncio
async def test_valid_payment(mock_rpc):
    result = await service.verify_solana_payment(
        REFERENCE,
        RECIPIENT,
        MINT,
        Decimal("10.50"),
    )

    assert result == SIGNATURE
    mock_rpc[0].assert_awaited_once_with(REFERENCE)

@pytest.mark.asyncio
async def test_wrong_destination(mock_rpc):
    transaction = make_transaction()
    transaction["transaction"]["message"]["instructions"][0]["parsed"]["info"][
        "destination"
    ] = "wrong-token-account"

    mock_rpc[1].return_value = transaction

    result = await service.verify_solana_payment(
        REFERENCE,
        RECIPIENT,
        MINT,
        Decimal("10.50"),
    )

    assert result is None

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "changes",
    [
        {"recipient": "wrong-wallet"},
        {"mint": "wrong-mint"},
        {"amount": "9.50"},
        {"recipient": "wrong-wallet"},
        {"error": {"InstructionError": [0, "InvalidArgument"]}},
    ],
)
async def test_invalid_payment(mock_rpc, changes):
    mock_rpc[1].return_value = make_transaction(**changes)

    result = await service.verify_solana_payment(
        REFERENCE,
        RECIPIENT,
        MINT,
        Decimal("10.50"),
    )

    assert result is None


@pytest.mark.asyncio
async def test_no_transactions(mock_rpc):
    mock_rpc[0].return_value = []

    result = await service.verify_solana_payment(
        REFERENCE,
        RECIPIENT,
        MINT,
        Decimal("10.50"),
    )

    assert result is None
