# src/nadfun_sdk/exceptions.py

class RPCConnectionError(RuntimeError):
    """RPC 연결 실패 등 네트워크 초기화 에러."""

class PermitNotSupportedError(RuntimeError):
    """토큰이 EIP-2612(permit)를 지원하지 않는 경우."""

class ABIError(RuntimeError):
    """ABI가 실제 컨트랙트 시그니처와 맞지 않는 경우."""

class RouteSelectionError(RuntimeError):
    """AUTO 라우팅 판단 중 발생한 문제."""
