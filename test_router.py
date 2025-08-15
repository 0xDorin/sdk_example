# test_router.py
from nadfun_sdk import NadfunSDK, router
import time

from nadfun_sdk.types import BuyParams

# 설정
RPC_URL = "..."  # RPC URL 입력
PRIVATE_KEY = "0x..."  # 프라이빗 키 입력
MY_ADDRESS = "0x..."

# 라우터 초기화
sdk = NadfunSDK(RPC_URL, PRIVATE_KEY)

# 테스트할 토큰
TOKEN_ADDRESS = "0x62f0956153dD2261E97f32d505eE6aAca671D61e" 

def test_buy(amount_in_wei):
    print("\n=== BUY 테스트 ===")
    
    # 구매할 양 (wei 단위)
    amount_in_wei = int(amount_in_wei * 10**18)  # 0.1 MON
    
    # 먼저 예상 출력 확인
    router_addr, amount_out = sdk.get_amount_out(TOKEN_ADDRESS, amount_in_wei, is_buy=True)
    print(f"라우터: {router_addr}")
    print(f"예상 토큰 수량: {amount_out}")
    
    # Buy 파라미터
    buy_params = {
        "token": TOKEN_ADDRESS,
        "to": MY_ADDRESS,  # 본인 주소로 받기
        "amount_in": amount_in_wei,
        "amount_out_min": int(amount_out * 0.95),  # 5% 슬리피지
        "deadline": int(time.time()) + 300  # 5분 후 만료
    }
    
    try:
        tx_hash = sdk.buy(router_addr, buy_params)
        print(f"Buy 트랜잭션 전송됨: {tx_hash}")
        return tx_hash
    except Exception as e:
        print(f"Buy 실패: {e}")
        return None

def test_sell():
    print("\n=== SELL 테스트 ===")
    
    # 판매할 토큰 양
    amount_in_tokens = int(1000 * 10**18)  # 1000 토큰 (decimals 확인 필요)
    
    # 먼저 예상 출력 확인
    router_addr, amount_out = sdk.get_amount_out(TOKEN_ADDRESS, amount_in_tokens, is_buy=False)
    print(f"라우터: {router_addr}")
    print(f"예상 MON 수량: {amount_out}")
    
    # Sell 파라미터
    sell_params = {
        "token": TOKEN_ADDRESS,
        "to": MY_ADDRESS,  # 본인 주소로 받기
        "amount_in": amount_in_tokens,
        "amount_out_min": int(amount_out * 0.95),  # 5% 슬리피지
        "deadline": int(time.time()) + 300  # 5분 후 만료
    }
    
    try:
        tx_hash = sdk.sell(router_addr, sell_params)
        print(f"Sell 트랜잭션 전송됨: {tx_hash}")
        return tx_hash
    except Exception as e:
        print(f"Sell 실패: {e}")
        return None

def test_quotes(buyAmount, sellAmount):
    print("\n=== 가격 조회 테스트 ===")
    
    # Buy 가격 조회
    amount_in = int(buyAmount * 10**18)  # 0.01 MON
    router_addr, amount_out = sdk.get_amount_out(TOKEN_ADDRESS, amount_in, is_buy=True)
    print(f"Buy - 입력: {amount_in / 10**18} MON, 출력: {amount_out / 10**18} 토큰, 라우터: {router_addr}")
    
    # Sell 가격 조회
    amount_in = int(sellAmount * 10**18)  # 1000 토큰
    router_addr, amount_out = sdk.get_amount_out(TOKEN_ADDRESS, amount_in, is_buy=False)
    print(f"Sell - 입력: {amount_in / 10**18} 토큰, 출력: {amount_out / 10**18} MON, 라우터: {router_addr}")

if __name__ == "__main__":
    # 가격 조회 테스트

    buyAmount = 1
    sellAmount = 1000

    test_quotes(buyAmount, sellAmount)
    
    # Buy 테스트
    test_buy(buyAmount)
    
    # Sell 테스트 (토큰 approve 필요)
    # test_sell()
    
    print("\n테스트 완료!")

    