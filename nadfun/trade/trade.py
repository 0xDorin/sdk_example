import time
from typing import Dict, Any, TYPE_CHECKING
from web3 import Web3
from eth_account.messages import encode_defunct

if TYPE_CHECKING:
    from ..router import NadfunRouter

from ..types import (
    BuyParams,
    SellPermitParams,
    RouteType
)


class TradingModule:
    def __init__(self, router: 'NadfunRouter'):
        self.router = router
        self.w3 = router.w3
    
    async def buy(self, params: BuyParams) -> Dict[str, Any]:
        """
        Execute buy transaction
        
        Args:
            params: Buy parameters
        
        Returns:
            Transaction receipt
        """
        return await self.router.buy(params)
    
    async def sell(self, params: SellPermitParams) -> Dict[str, Any]:
        """
        Execute sell transaction with permit
        
        Args:
            params: Sell parameters with permit
        
        Returns:
            Transaction receipt
        """
        return await self.router.sell(params)
    
    async def get_amount_out(self, token: str, amount_in: int, is_buy: bool = True) -> int:
        """
        Calculate output amount for given input
        
        Args:
            token: Token address
            amount_in: Input amount
            is_buy: True for buy, False for sell
        
        Returns:
            Output amount
        """
        return await self.router.get_amount_out(token, amount_in, is_buy)
    
    async def get_amount_in(self, token: str, amount_out: int, is_buy: bool = True) -> int:
        """
        Calculate input amount for given output
        
        Args:
            token: Token address
            amount_out: Desired output amount
            is_buy: True for buy, False for sell
        
        Returns:
            Required input amount
        """
        return await self.router.get_amount_in(token, amount_out, is_buy)
    
    def create_permit_signature(
        self,
        token: str,
        spender: str,
        amount: int,
        deadline: int,
        nonce: int = 0
    ) -> Dict[str, Any]:
        """
        Create EIP-2612 permit signature
        
        Args:
            token: Token address
            spender: Spender address
            amount: Amount to approve
            deadline: Deadline timestamp
            nonce: Nonce (default 0)
        
        Returns:
            Dict with v, r, s signature components
        """
        # Domain separator for EIP-712
        domain = {
            'name': 'Token',  # This should be fetched from token contract
            'version': '1',
            'chainId': self.w3.eth.chain_id,
            'verifyingContract': Web3.to_checksum_address(token)
        }
        
        # Permit type
        permit_type = {
            'Permit': [
                {'name': 'owner', 'type': 'address'},
                {'name': 'spender', 'type': 'address'},
                {'name': 'value', 'type': 'uint256'},
                {'name': 'nonce', 'type': 'uint256'},
                {'name': 'deadline', 'type': 'uint256'}
            ]
        }
        
        # Permit values
        permit_values = {
            'owner': self.router.address,
            'spender': Web3.to_checksum_address(spender),
            'value': amount,
            'nonce': nonce,
            'deadline': deadline
        }
        
        # Create structured data
        from eth_account.messages import encode_structured_data
        structured_data = {
            'types': {
                'EIP712Domain': [
                    {'name': 'name', 'type': 'string'},
                    {'name': 'version', 'type': 'string'},
                    {'name': 'chainId', 'type': 'uint256'},
                    {'name': 'verifyingContract', 'type': 'address'}
                ],
                **permit_type
            },
            'primaryType': 'Permit',
            'domain': domain,
            'message': permit_values
        }
        
        # Sign the structured data
        encoded_data = encode_structured_data(structured_data)
        signed_message = self.w3.eth.account.sign_message(
            encoded_data,
            private_key=self.router.private_key
        )
        
        # Extract v, r, s
        v = signed_message.v
        r = '0x' + signed_message.r.to_bytes(32, byteorder='big').hex()
        s = '0x' + signed_message.s.to_bytes(32, byteorder='big').hex()
        
        return {
            'v': v,
            'r': r,
            's': s
        }
    
    def prepare_sell_permit_params(
        self,
        token: str,
        amount_in: int,
        amount_out_min: int,
        to: str = None,
        deadline: int = None
    ) -> SellPermitParams:
        """
        Prepare sell parameters with permit signature
        
        Args:
            token: Token address
            amount_in: Amount to sell
            amount_out_min: Minimum output amount
            to: Recipient address (optional)
            deadline: Deadline timestamp (optional)
        
        Returns:
            SellPermitParams with signature
        """
        if deadline is None:
            deadline = int(time.time()) + 300  # 5 minutes from now
        
        # Determine router address based on token status
        is_listed = self.router.is_listed(token)  # This should be async in real implementation
        router_address = self.router.dex_router_address if is_listed else self.router.bonding_curve_router_address
        
        # Create permit signature
        signature = self.create_permit_signature(
            token=token,
            spender=router_address,
            amount=amount_in,
            deadline=deadline
        )
        
        return SellPermitParams(
            amount_in=amount_in,
            amount_out_min=amount_out_min,
            amount_allowance=amount_in,
            token=token,
            to=to or self.router.address,
            deadline=deadline,
            v=signature['v'],
            r=signature['r'],
            s=signature['s']
        )