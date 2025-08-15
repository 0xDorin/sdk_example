import json
import os
from typing import Dict, Any

_ABI_DIR = os.path.join(os.path.dirname(__file__), "abis")

# 현재 네 파일명에 맞게 매핑 (필요하면 바꿔도 됨)
_FILEMAP = {
    "router":      "Router.json",          # DEX/Curve 라우터 (buy/sell 동일 시그니처)
    "wrapper":  "wrapperContract.json", # wrapper getAmountIn/Out
    "erc20Permit":           "erc20Permit.json",     # ERC20 + Permit
}

def _load_json(path: str) -> Any:
    if not os.path.exists(path):
        raise FileNotFoundError(f"ABI file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_default_abis() -> Dict[str, Any]:
    """
    Returns:
        {
          "dex_router": [...],
          "curve_router": [...],
          "wrapper_router": [...],
          "erc20": [...]
        }
    """
    out: Dict[str, Any] = {}
    for key, fname in _FILEMAP.items():
        out[key] = _load_json(os.path.join(_ABI_DIR, fname))
    return out
