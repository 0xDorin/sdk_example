# src/nadfun_sdk/constants.py

MAX_UINT256 = (1 << 256) - 1

# 기본 가스전략(아주 보수적). 프로덕션에서는 외부 가스 오라클/전략 권장.
DEFAULT_PRIORITY_FEE_DIVISOR = 10  # baseGas / 10
