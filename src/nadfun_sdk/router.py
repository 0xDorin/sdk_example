# src/nadfun_sdk/router.py
from dataclasses import asdict, is_dataclass
from typing import Union, Tuple
from web3 import Web3
from eth_account import Account
from eth_utils import function_signature_to_4byte_selector, to_checksum_address
from eth_abi import encode

from .types import BuyParams, SellParams, CurveData
from .abi_loader import load_default_abis

def to_checksum(addr: str) -> str:
    return to_checksum_address(addr)

ParamsLike = Union[dict, BuyParams, SellParams]

class NadfunSDK:

    wrapperContractAddress = "0xD47Dd1a82dd239688ECE1BA94D86f3D32960C339"
    """
    - 라우팅/쿼트는 wrapper.getAmount{Out,In}에서 (routerAddr, amount)로 받아서 사용
    - 슬리피지/퍼밋 제거
    - buy/sell만 지원 (각 라우터의 params(tuple) 시그니처 사용)
    """

    def __init__(self, rpc_url: str, private_key: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise RuntimeError("RPC 연결 실패")

        self.account: Account = Account.from_key(private_key)
        self.address: str = self.account.address

        abis = load_default_abis()

        self.wrapper = self.w3.eth.contract(address=to_checksum(self.wrapperContractAddress), abi=abis["wrapper"])
        self.erc20_abi = abis["erc20Permit"]

    def _send_tx_with_calldata(self, to: str, calldata: bytes, value: int = 0) -> str:
        """Low-level call로 트랜잭션 전송"""
        tx = {
            'from': self.account.address,
            'to': to_checksum(to),
            'data': calldata.hex(),
            'value': value,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': self.w3.eth.chain_id
        }
        
        # gas 추정
        tx['gas'] = int(self.w3.eth.estimate_gas(tx) * 1.2)
        
        # EIP-1559 수수료
        block = self.w3.eth.get_block('latest')
        base_fee = block.get('baseFeePerGas', 0)
        if base_fee:
            tx['maxPriorityFeePerGas'] = self.w3.to_wei(1, 'gwei')
            tx['maxFeePerGas'] = base_fee * 2 + tx['maxPriorityFeePerGas']
        else:
            tx['gasPrice'] = self.w3.eth.gas_price
        
        signed = self.account.sign_transaction(tx)
        # rawTransaction 속성 대신 raw_transaction 사용 (버전 호환성)
        raw_tx = signed.raw_transaction if hasattr(signed, 'raw_transaction') else signed.rawTransaction
        return self.w3.eth.send_raw_transaction(raw_tx).hex()

    # -------------------------- 조회 --------------------------
    def get_curves(self, token: str) -> CurveData:
        # 기존처럼 curve 컨트랙트에서 curves(...) 읽는 로직이 필요하면 유지
        res = self.curve.functions.curves(to_checksum(token)).call()
        return CurveData(
            realMonReserve=res[0],
            realTokenReserve=res[1],
            virtualMonReserve=res[2],
            virtualTokenReserve=res[3],
            k=res[4],
            targetTokenAmount=res[5],
            initVirtualMonReserve=res[6],
            initVirtualTokenReserve=res[7],
        )

    # -------------------------- wrapper 기반 가격 --------------------------
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

    # -------------------------- 거래 --------------------------
    def buy(self, router_addr: str, params: ParamsLike) -> str:
        p = asdict(params) if is_dataclass(params) else dict(params)
        
        # 파라미터 추출
        router_cs = to_checksum(router_addr)  # 함수 파라미터로 받은 router 주소
        token_cs = to_checksum(p["token"])
        to_cs = to_checksum(p["to"])
        user_min = int(p["amount_out_min"])
        amount_in = int(p["amount_in"])
        deadline = int(p["deadline"])
        
        # buy 함수 시그니처와 파라미터 인코딩
        # buy((uint256,address,address,uint256))
        selector = function_signature_to_4byte_selector("buy((uint256,address,address,uint256))")
        
        # tuple 파라미터 인코딩
        encoded_params = encode(
            ['(uint256,address,address,uint256)'],
            [(user_min, token_cs, to_cs, deadline)]
        )
        
        calldata = selector + encoded_params
        
        # 트랜잭션 전송 (value 포함)
        return self._send_tx_with_calldata(router_cs, calldata, value=amount_in)

    def sell(self, router_addr: str, params: ParamsLike) -> str:
        p = asdict(params) if is_dataclass(params) else dict(params)
        
        # 파라미터 추출
        router_cs = to_checksum(router_addr)  # 함수 파라미터로 받은 router 주소
        token_cs = to_checksum(p["token"])
        to_cs = to_checksum(p["to"])
        user_min = int(p["amount_out_min"])
        amount_in = int(p["amount_in"])
        deadline = int(p["deadline"])
        
        # sell 함수 시그니처와 파라미터 인코딩
        # sell((uint256,uint256,address,address,uint256))
        selector = function_signature_to_4byte_selector("sell((uint256,uint256,address,address,uint256))")
        
        # tuple 파라미터 인코딩
        encoded_params = encode(
            ['(uint256,uint256,address,address,uint256)'],
            [(amount_in, user_min, token_cs, to_cs, deadline)]
        )
        
        calldata = selector + encoded_params
        
        # 트랜잭션 전송 (sell은 value 없음)
        return self._send_tx_with_calldata(router_cs, calldata)
