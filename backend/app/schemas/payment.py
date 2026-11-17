from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field
from pydantic import field_validator
from app.libs.solana import is_valid_solana_address

class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=6)
    currency: Literal["USDC"]
    network: Literal["solana-devnet"]
    recipient_address: str = Field(min_length=32, max_length=44)
    
    @field_validator("recipient_address")
    @classmethod
    def validate_recipient_address(cls, value: str) -> str:
        if not is_valid_solana_address(value):
            raise ValueError("Invalid Solana wallet address")

        return value


class PaymentResponse(PaymentCreate):
    id: str
    reference: str
    payment_url: str
    status: Literal["pending"]