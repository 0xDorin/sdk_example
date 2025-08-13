# Nadfun SDK

Python SDK for interacting with the Nadfun trading platform.

## 설치

```bash
pip install nadfun-sdk
```

## 사용법

### 기본 사용 예시

```python
from nadfun_sdk import NadfunRouter
from nadfun_sdk.types import BuyParams, RouterType

# 라우터 초기화
router = NadfunRouter(
    private_key="your_private_key",
    router_type=RouterType.UNISWAP_V2
)

# 토큰 매수
buy_params = BuyParams(
    token_address="0x...",
    amount_in="1000000000000000000",  # 1 ETH in wei
    min_amount_out="0",
    deadline=1234567890
)

tx_hash = router.buy(buy_params)
print(f"매수 트랜잭션: {tx_hash}")
```

### 매도 예시

```python
from nadfun_sdk.types import SellPermitParams

# Permit을 사용한 매도
sell_params = SellPermitParams(
    token_address="0x...",
    amount="1000000000000000000",  # 1 token
    min_amount_out="0",
    deadline=1234567890,
    permit_deadline=1234567890,
    v=27,
    r="0x...",
    s="0x..."
)

tx_hash = router.sell_with_permit(sell_params)
print(f"매도 트랜잭션: {tx_hash}")
```

## 기능

- ✅ 토큰 매수/매도
- ✅ EIP-2612 Permit 지원
- ✅ 다양한 DEX 라우터 지원 (Uniswap V2/V3, SushiSwap 등)
- ✅ 가스 최적화
- ✅ 타입 안전성

## 라이선스

MIT License
