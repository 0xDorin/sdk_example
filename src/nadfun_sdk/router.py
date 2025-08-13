from dataclasses import asdict, is_dataclass
from typing import Union

from web3 import Web3
from eth_account import Account

from .types import BuyParams, SellPermitParams, CurveData
from .constants import MAX_UINT256
from .utils import (
    to_checksum,
    apply_slippage,
    build_permit_signature,
    send_function_tx,         # ✅ 새 유틸
)
from .abi_loader import load_default_abis
from .config import NETWORKS

ParamsLike = Union[dict, BuyParams, SellPermitParams]

class NadfunRouter:
    def __init__(self, rpc_url: str, private_key: str, network: str = "monad_testnet"):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise RuntimeError("RPC 연결 실패")

        self.account: Account = Account.from_key(private_key)
        self.address: str = self.account.address

        addrs = NETWORKS.get(network)
        if not addrs:
            raise ValueError(f"지원하지 않는 네트워크: {network}")

        abis = load_default_abis()
        self.dex = self.w3.eth.contract(address=to_checksum(addrs["DEX_ROUTER"]),  abi=abis["dex_router"])
        self.curve = self.w3.eth.contract(address=to_checksum(addrs["CURVE_ROUTER"]), abi=abis["curve_router"])
        self.erc20_abi = abis["erc20"]
        self.dex_address = to_checksum(addrs["DEX_ROUTER"])
        self.curve_address = to_checksum(addrs["CURVE_ROUTER"])

    # …(get_curves / is_lock / is_listing / get_amount_* 동일)

    def _router_for(self, token_cs: str):
        return self.dex if bool(self.curve.functions.isListed(token_cs).call()) else self.curve

    def _expected_min_out(self, token_cs: str, amount_in: int, is_buy: bool, sp: int) -> int:
        expected = self.get_amount_out(token_cs, amount_in, is_buy)
        return apply_slippage(expected, sp)

    def _slippage_percent_or_default(self, p: dict) -> int:
        sp = p.get("slippage_percent")
        try:
            return 0 if sp is None else int(sp)
        except Exception:
            return 0

    def buy(self, params: ParamsLike) -> str:
        p = asdict(params) if is_dataclass(params) else dict(params)
        token_cs = to_checksum(p["token"])
        router = self._router_for(token_cs)

        sp = self._slippage_percent_or_default(p)
        expected_min_out = self._expected_min_out(token_cs, int(p["amount_in"]), True, sp)
        user_min = int(p["amount_out_min"])
        if expected_min_out < user_min:
            raise ValueError(
                f"[BUY] expected_min_out({expected_min_out}) < amount_out_min({user_min})"
            )

        fn = router.functions.buy(
            to_checksum(p["to"]),
            token_cs,
            user_min,
        )
        # ✅ 한 줄로 전송 (value 포함)
        return send_function_tx(self.w3, self.account, fn, overrides={"value": int(p["amount_in"])})

    def sell(self, params: ParamsLike) -> str:
        p = asdict(params) if is_dataclass(params) else dict(params)
        token_cs = to_checksum(p["token"])

        route_is_dex = bool(self.curve.functions.isListed(token_cs).call())
        router = self.dex if route_is_dex else self.curve
        router_addr = self.dex_address if route_is_dex else self.curve_address

        sp = self._slippage_percent_or_default(p)
        expected_min_out = self._expected_min_out(token_cs, int(p["amount_in"]), False, sp)
        user_min = int(p["amount_out_min"])
        if expected_min_out < user_min:
            raise ValueError(
                f"[SELL] expected_min_out({expected_min_out}) < amount_out_min({user_min})"
            )

        allowance = int(p.get("amount_allowance") or MAX_UINT256)
        v, r, s = p.get("v"), p.get("r"), p.get("s")
        if v is None or r is None or s is None:
            v, r, s = build_permit_signature(
                w3=self.w3,
                account=self.account,
                token=token_cs,
                owner=self.address,
                spender=router_addr,
                value=allowance,
                deadline=int(p["deadline"]),
                erc20_abi=self.erc20_abi,
            )

        fn = router.functions.sellPermit(
            to_checksum(p["to"]),
            token_cs,
            int(p["amount_in"]),
            user_min,
            int(p["deadline"]),
            allowance,
            int(v), r, s,
        )
        # ✅ 한 줄로 전송
        return send_function_tx(self.w3, self.account, fn)
