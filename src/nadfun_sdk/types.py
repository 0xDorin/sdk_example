from dataclasses import dataclass
from typing import Optional

@dataclass
class BuyParams:
    token: str
    to: str
    amount_out_min: int
    amount_in: int
    deadline: int
    slippage_percent: Optional[int] = None  # 검증용 옵션 (기본 0%)

@dataclass
class SellPermitParams:
    token: str
    to: str
    amount_in: int
    amount_out_min: int
    deadline: int
    amount_allowance: Optional[int] = None
    v: Optional[int] = None
    r: Optional[bytes] = None
    s: Optional[bytes] = None
    slippage_percent: Optional[int] = None  # 검증용 옵션 (기본 0%)

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
