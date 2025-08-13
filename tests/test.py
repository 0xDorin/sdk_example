import os
from time import time
from nadfun_sdk.router import NadfunRouter

RPC = os.environ["NAD_RPC"]
PK  = os.environ["NAD_PK"]

# 실제 토큰/수량으로 교체
TOKEN = "0xYourTokenAddress"
TO    = "0xYourReceiverAddress"  # 보통 본인 주소
AMOUNT_IN_WEI = 10**16           # 예: 0.01 (체인 기준 18dec면 1e16)
SLIPPAGE_PERCENT = 30            # 30% = 기대수량의 70%
DEADLINE = int(time()) + 60 * 10 # 10분

sdk = NadfunRouter(RPC, PK, network="monad_testnet")

# 1) 기본 조회
print("listed?", sdk.is_listing(TOKEN))
print("locked?", sdk.is_lock(TOKEN))
curves = sdk.get_curves(TOKEN)
print("curves.k =", curves.k)

# 2) 가격 시뮬 (buy / sell)
buy_quote  = sdk.get_amount_out(TOKEN, AMOUNT_IN_WEI, is_buy=True)
sell_quote = sdk.get_amount_out(TOKEN, AMOUNT_IN_WEI, is_buy=False)
print("buy_quote:", buy_quote)
print("sell_quote:", sell_quote)

# 3) 매수 실행 (유저가 정한 minOut을 꼭 넣는다)
user_min_out_buy = (buy_quote * (100 - SLIPPAGE_PERCENT)) // 100
print("user_min_out_buy:", user_min_out_buy)

tx_hash_buy = sdk.buy({
    "token": TOKEN,
    "to": TO,
    "amount_out_min": user_min_out_buy,  # ← 유저 기준
    "amount_in": AMOUNT_IN_WEI,
    "deadline": DEADLINE,
    "slippage_percent": SLIPPAGE_PERCENT,  # ← SDK 내부 검증용
})
print("BUY sent:", tx_hash_buy)

# (선택) 영수증 대기
rcpt_buy = sdk.w3.eth.wait_for_transaction_receipt(tx_hash_buy)
print("BUY status:", rcpt_buy.status)

# 4) 매도 실행 (permit 자동 생성; 토큰이 EIP-2612 지원해야 함)
user_min_out_sell = (sell_quote * (100 - SLIPPAGE_PERCENT)) // 100
print("user_min_out_sell:", user_min_out_sell)

tx_hash_sell = sdk.sell({
    "token": TOKEN,
    "to": TO,
    "amount_in": AMOUNT_IN_WEI,
    "amount_out_min": user_min_out_sell,
    "deadline": DEADLINE,
    "slippage_percent": SLIPPAGE_PERCENT,  # ← SDK 내부 검증용
    # v/r/s를 생략하면 SDK가 permit 서명을 생성해 넣음
})
print("SELL sent:", tx_hash_sell)

rcpt_sell = sdk.w3.eth.wait_for_transaction_receipt(tx_hash_sell)
print("SELL status:", rcpt_sell.status)
