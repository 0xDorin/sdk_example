# src/nadfun_sdk/router.py
from typing import Tuple
from web3 import Web3
from eth_account import Account
from eth_utils import function_signature_to_4byte_selector, to_checksum_address
from eth_abi import encode
from .abi_loader import load_default_abis
import time

def to_checksum(addr: str) -> str:
    return to_checksum_address(addr)

class NadfunSDK:

    wrapperContractAddress = "0xD47Dd1a82dd239688ECE1BA94D86f3D32960C339"

    def __init__(self, rpc_url: str, private_key: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise RuntimeError("RPC connection failed")

        self.account: Account = Account.from_key(private_key)
        self.address: str = self.account.address

        self.buy_selector = function_signature_to_4byte_selector("buy((uint256,address,address,uint256))")
        self.sell_selector = function_signature_to_4byte_selector("sell((uint256,uint256,address,address,uint256))")

        self.gas_price = self.w3.eth.gas_price
        self.chain_id = self.w3.eth.chain_id

        abis = load_default_abis()

        self.wrapper = self.w3.eth.contract(address=to_checksum(self.wrapperContractAddress), abi=abis["wrapper"])
        self.erc20_abi = abis["erc20Permit"]

    def _send_tx_with_calldata(self, to: str, calldata: bytes, value: int = 0, is_buy: bool = True) -> str:
        tx = {
            'from': self.account.address,
            'to': to_checksum(to),
            'data': calldata.hex(),
            'value': value,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': self.chain_id
        }

        tx['gas'] = 261000 if is_buy else 232000
        tx['gasPrice'] = self.gas_price
        
        signed = self.account.sign_transaction(tx)
        raw_tx = signed.raw_transaction if hasattr(signed, 'raw_transaction') else signed.rawTransaction
        return self.w3.eth.send_raw_transaction(raw_tx).hex()

    # -------------------------- curve data --------------------------
    def get_curves(self, token: str) :
        res = self.curve.functions.curves(to_checksum(token)).call()
        return (
            res[0],
            res[1],
            res[2],
            res[3],
            res[4],
            res[5],
            res[6],
            res[7],
        )

    # -------------------------- wrapper based price --------------------------
    def get_amount_out(self, token: str, amount_in: int, is_buy: bool) -> Tuple[str, int]:
        token_cs = to_checksum(token)
        router_addr, amount_out = self.wrapper.functions.getAmountOut(
            token_cs, int(amount_in), bool(is_buy)
        ).call()
        return to_checksum(router_addr), int(amount_out)

    def get_amount_in(self, token: str, amount_out: int, is_buy: bool) -> Tuple[str, int]:
        token_cs = to_checksum(token)
        router_addr, amount_in = self.wrapper.functions.getAmountIn(
            token_cs, int(amount_out), bool(is_buy)
        ).call()
        return to_checksum(router_addr), int(amount_in)

    # -------------------------- trade --------------------------
    def buy(self, router_addr: str, token_addr, to_addr, amount_in, amount_out_min) -> str:

        deadline = int(time.time()) + 300
        selector = self.buy_selector
        
        encoded_params = encode(
            ['(uint256,address,address,uint256)'],
            [(amount_out_min, token_addr, to_addr, deadline)]
        )
        
        calldata = selector + encoded_params
        
        # send transaction (value included)
        return self._send_tx_with_calldata(router_addr, calldata, value=amount_in, is_buy=True)

    def sell(self, router_addr: str, token_addr, to_addr, amount_in, amount_out_min) -> str:
        
        deadline = int(time.time()) + 300
        selector = self.sell_selector
        
        encoded_params = encode(
            ['(uint256,uint256,address,address,uint256)'],
            [(amount_in, amount_out_min, token_addr, to_addr, deadline)]
        )
        
        calldata = selector + encoded_params
        
        # send transaction (value not included)
        return self._send_tx_with_calldata(router_addr, calldata, is_buy=False)
