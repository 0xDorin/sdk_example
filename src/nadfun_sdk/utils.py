from typing import Tuple, Optional, Dict, Any
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_structured_data
from eth_utils import to_checksum_address, to_bytes

def to_checksum(addr: str) -> str:
    return to_checksum_address(addr)

# ─────────────────────────────────────────────────────────
# EIP-1559 트랜잭션 빌드 + 서명 + 전송 (원샷)
# ─────────────────────────────────────────────────────────
# utils.py
def _with_eip1559_defaults(w3, account, tx):
    tx = dict(tx)
    tx.setdefault("from", account.address)
    tx.setdefault("nonce", w3.eth.get_transaction_count(account.address))
    tx.setdefault("chainId", w3.eth.chain_id)

    # gas limit: 계속 추정하세요 (권장), 필요시 1.2 배 여유
    if "gas" not in tx:
        est = w3.eth.estimate_gas(tx)
        tx["gas"] = int(est * 12 // 10)  # +20% 버퍼 (옵션)

    # EIP-1559 수수료 기본치
    if "maxFeePerGas" not in tx or "maxPriorityFeePerGas" not in tx:
        block = w3.eth.get_block("latest")
        base = block.get("baseFeePerGas")
        if base is not None:
            tip = w3.to_wei(1, "gwei")  # 네트워크에 맞게 조정
            tx["maxPriorityFeePerGas"] = tip
            tx["maxFeePerGas"] = base * 2 + tip
        else:
            # EIP-1559 미지원 체인: 레거시 fallback
            if "gasPrice" not in tx:
                tx["gasPrice"] = w3.eth.gas_price
    return tx



def send_function_tx(
    w3: Web3,
    account: Account,
    fn,                          # web3.contract.functions.<fn>(...)
    overrides: Optional[Dict[str, Any]] = None,  # {"value": ..., "gas": ..., ...}
) -> str:
    """
    컨트랙트 함수 호출을 트랜잭션으로 전송:
    - build_transaction + 가스/수수료 채우기 + 서명 + send
    - 반환: tx hash(hex)
    """
    base = overrides or {}
    tx = fn.build_transaction(_with_eip1559_defaults(w3, account, base))
    signed = account.sign_transaction(tx)
    return w3.eth.send_raw_transaction(signed.rawTransaction).hex()

# ─────────────────────────────────────────────────────────
# Slippage
# ─────────────────────────────────────────────────────────
def apply_slippage(expected_amount: int, slippage_percent: int) -> int:
    sp = 0 if slippage_percent is None else int(slippage_percent)
    if sp < 0: sp = 0
    if sp > 100: sp = 100
    return (int(expected_amount) * (100 - sp)) // 100

# ─────────────────────────────────────────────────────────
# Permit (EIP-2612)
# ─────────────────────────────────────────────────────────
def _erc20(w3: Web3, token: str, erc20_abi: list):
    return w3.eth.contract(address=to_checksum(token), abi=erc20_abi)

def _erc20_name(token_c) -> str:
    try:
        return token_c.functions.name().call()
    except Exception:
        try:
            raw = token_c.functions.name().call()
            if isinstance(raw, (bytes, bytearray)):
                return raw.rstrip(b"\x00").decode("utf-8", errors="ignore") or "Token"
        except Exception:
            pass
    return "Token"

def _erc20_nonce(token_c, owner: str) -> int:
    try:
        return int(token_c.functions.nonces(owner).call())
    except Exception:
        try:
            return int(token_c.functions._nonces(owner).call())
        except Exception as e:
            raise RuntimeError("토큰이 EIP-2612 nonce 메서드를 지원하지 않습니다") from e

def build_permit_signature(
    w3: Web3,
    account: Account,
    token: str,
    owner: str,
    spender: str,
    value: int,
    deadline: int,
    erc20_abi: list,
) -> Tuple[int, bytes, bytes]:
    token_c = _erc20(w3, token, erc20_abi)
    name = _erc20_name(token_c)
    chain_id = w3.eth.chain_id
    nonce = _erc20_nonce(token_c, owner)

    domain = {
        "name": name,
        "version": "1",
        "chainId": chain_id,
        "verifyingContract": to_checksum(token),
    }
    types = {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
            {"name": "version", "type": "string"},
            {"name": "chainId", "type": "uint256"},
            {"name": "verifyingContract", "type": "address"},
        ],
        "Permit": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"},
            {"name": "nonce", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
        ],
    }
    message = {
        "owner": owner,
        "spender": spender,
        "value": int(value),
        "nonce": int(nonce),
        "deadline": int(deadline),
    }
    structured = {
        "types": types,
        "domain": domain,
        "primaryType": "Permit",
        "message": message,
    }
    signable = encode_structured_data(structured)
    signed = account.sign_message(signable)
    return signed.v, to_bytes(hexstr=signed.r.hex()), to_bytes(hexstr=signed.s.hex())
