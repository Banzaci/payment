
from typing import Literal

from pydantic import BaseModel, Field


PaymentMethod = Literal[
    "usdc",
    "usdt",
    "card",
    "apple_pay",
    "google_pay",
    "mobile_money",
]


class MerchantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    default_currency: str = Field(min_length=3, max_length=10)
    enabled_payment_methods: list[PaymentMethod] = Field(
        default_factory=list,
    )


class MerchantResponse(BaseModel):
    id: str
    name: str
    default_currency: str
    enabled_payment_methods: list[PaymentMethod]
    api_key: str
