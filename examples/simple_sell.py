from nadfun_sdk import NadfunSDK
from dotenv import load_dotenv
import os

load_dotenv()

# config
RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
MY_ADDRESS = os.getenv("MY_ADDRESS")

# sdk init
sdk = NadfunSDK(RPC_URL, PRIVATE_KEY)

# MEME_TOKEN
TOKEN_ADDRESS = "0x62f0956153dD2261E97f32d505eE6aAca671D61e" 

print("\n=== SELL TEST ===")
    
# sell amount (wei)
amount_in_wei = 1000000 * 10**18 # 1000000 MEME
    
# get amount out
router_addr, amount_out = sdk.get_amount_out(TOKEN_ADDRESS, amount_in_wei, is_buy=False)
print(f"router_addr: {router_addr}")
print(f"amount_out: {amount_out}")

# slippage
amount_out = int(amount_out * 0.8)
    
try:
    tx_hash = sdk.sell(router_addr, TOKEN_ADDRESS, MY_ADDRESS, amount_in_wei, amount_out)
    print(f"Sell tx_hash: {tx_hash}")
except Exception as e:
    print(f"Sell error: {e}")