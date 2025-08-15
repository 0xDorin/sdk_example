from dataclasses import dataclass
from typing import Optional

@dataclass
class BuyParams:
    token: str
    to: str
    amount_out_min: int
    amount_in: int
    deadline: int

@dataclass
class SellParams:
    token: str
    to: str
    amount_in: int
    amount_out_min: int
    deadline: int

@dataclass
class CurveData:
    realMonReserve: int
    realTokenReserve: int
    virtualMonReserve: int
    virtualTokenReserve: int
    k: int
    targetTokenAmount: int
    initVirtualMonReserve: int
    initVirtualTokenReserve: int
