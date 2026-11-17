from decimal import Decimal

from app.libs.solana_rpc import (
    get_signatures_for_address,
    get_transaction,
)

async def verify_solana_payment(
    reference: str,
    recipient: str,
    mint: str,
    amount: Decimal,
) -> str | None:
    signatures = await get_signatures_for_address(reference)

    for item in signatures:
        if item.get("err") is not None:
            continue

        transaction = await get_transaction(item["signature"])

        if not transaction:
            continue

        meta = transaction.get("meta") or {}

        if meta.get("err") is not None:
            continue

        message = transaction.get("transaction", {}).get("message", {})
        instructions = message.get("instructions", [])

        for instruction in instructions:
            parsed = instruction.get("parsed")

            if not isinstance(parsed, dict):
                continue

            if parsed.get("type") not in {
                "transfer",
                "transferChecked",
            }:
                continue

            info = parsed.get("info", {})

            if parsed["type"] == "transferChecked":
                if info.get("mint") != mint:
                    continue

                if Decimal(
                    info.get("tokenAmount", {}).get("uiAmountString", "0")
                ) != amount:
                    continue

                destination = info.get("destination")

            else:
                # En vanlig SPL-transfer saknar mint och decimals
                # i instruktionen och kan därför inte verifieras
                # säkert med enbart dessa uppgifter.
                continue

            # Destination är ett tokenkonto, inte plånbokens adress.
            # Vi verifierar därför ägaren via tokenbalanserna.
            post_balances = meta.get("postTokenBalances", [])
            account_keys = message.get("accountKeys", [])

            for balance in post_balances:
                if balance.get("mint") != mint:
                    continue

                if balance.get("owner") != recipient:
                    continue

                index = balance.get("accountIndex")

                if not isinstance(index, int):
                    continue

                if index >= len(account_keys):
                    continue

                key = account_keys[index]
                address = (
                    key.get("pubkey")
                    if isinstance(key, dict)
                    else key
                )

                if address == destination:
                    
                    pre_balances = meta.get(
                        "preTokenBalances", []
                    )

                    pre_amount = Decimal("0")
                    post_amount = Decimal(
                        balance["uiTokenAmount"]["amount"]
                    )

                    decimals = balance[
                        "uiTokenAmount"
                    ]["decimals"]

                    for previous in pre_balances:
                        if previous.get("accountIndex") == index:
                            pre_amount = Decimal(
                                previous["uiTokenAmount"]["amount"]
                            )
                            break

                    received = (
                        post_amount - pre_amount
                    ) / (Decimal(10) ** decimals)

                    if received != amount:
                        continue

                    return item["signature"]

    return None
