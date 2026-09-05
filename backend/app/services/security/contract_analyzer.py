"""Contract analyzer for detecting malicious token contracts."""

import logging
from typing import Optional
from app.services.security.models import ContractAnalysisResult
from app.adapters.solana_rpc import SolanaRPCClient, TOKEN_2022_PROGRAM_ID

logger = logging.getLogger(__name__)


class ContractAnalyzer:
    """Analyze token contract for malicious patterns.
    
    Detects:
    - Transfer fee (hidden tax)
    - Mint authority (unlimited dilution)
    - Freeze authority (liquidity lock)
    - Known honeypot patterns
    """
    
    def __init__(self, rpc_client: Optional[SolanaRPCClient] = None):
        """Initialize contract analyzer."""
        # Known honeypot contract signatures (would be expanded in production)
        self.known_honeypots = set()
        self.rpc = rpc_client or SolanaRPCClient()
    
    async def analyze(
        self,
        chain: str,
        token_address: str,
    ) -> ContractAnalysisResult:
        """
        Analyze token contract for:
        1. Transfer fee (hidden tax)
        2. Mint authority (can dilute)
        3. Freeze authority (can freeze)
        4. Known honeypot patterns
        
        Args:
            chain: "solana"
            token_address: Token mint address
        
        Returns:
            ContractAnalysisResult
        """
        try:
            # Step 1: Check against known honeypots
            known_honeypot = token_address in self.known_honeypots
            
            # Unknown critical mint state is fail-closed.
            mint_info = await self.rpc.get_mint(token_address)
            if not mint_info:
                return ContractAnalysisResult(
                    is_blocked=False,
                    is_unknown=True,
                    risk_score=100,
                    contract_address=token_address,
                    reasons=["Critical on-chain mint data unavailable; trade deferred"],
                )
            extensions = mint_info.get("extensions") or []
            if mint_info.get("program_id") == TOKEN_2022_PROGRAM_ID and not isinstance(extensions, list):
                return ContractAnalysisResult(
                    is_blocked=False,
                    is_unknown=True,
                    risk_score=100,
                    contract_address=token_address,
                    reasons=["Token-2022 extensions could not be parsed; trade deferred"],
                )
            has_transfer_fee = any(
                isinstance(extension, dict)
                and extension.get("extension") == "transferFeeConfig"
                for extension in extensions
            )
            mint_authority = mint_info.get("mint_authority")
            freeze_authority = mint_info.get("freeze_authority")
            
            # Step 3: Calculate risk score
            risk_score = 0
            reasons = []
            
            if has_transfer_fee:
                risk_score += 30
                reasons.append("Transfer fee detected (hidden tax)")
            
            if mint_authority:
                risk_score += 25
                reasons.append(f"Mint authority active: {mint_authority}")
            
            if freeze_authority:
                risk_score += 15
                reasons.append(f"Freeze authority exists: {freeze_authority}")
            
            if known_honeypot:
                risk_score = 95
                reasons.append("Known honeypot pattern detected")
            
            # Cap at 100
            risk_score = min(risk_score, 100)
            
            is_blocked = known_honeypot or has_transfer_fee
            
            if is_blocked:
                logger.error(f"Contract analysis BLOCKED: {token_address} - {reasons}")
            else:
                logger.info(f"Contract analysis OK: {token_address} (score: {risk_score})")
            
            return ContractAnalysisResult(
                is_blocked=is_blocked,
                block_reason=f"Malicious contract detected" if is_blocked else None,
                risk_score=risk_score,
                contract_address=token_address,
                has_transfer_fee=has_transfer_fee,
                mint_authority=mint_authority,
                freeze_authority=freeze_authority,
                known_honeypot=known_honeypot,
                reasons=reasons,
                details={
                    'has_transfer_fee': has_transfer_fee,
                    'mint_authority': mint_authority,
                    'freeze_authority': freeze_authority,
                    'known_honeypot': known_honeypot,
                }
            )
        
        except Exception as e:
            logger.error(f"Contract analysis error: {e}")
            return ContractAnalysisResult(
                is_blocked=False,
                is_unknown=True,
                risk_score=100,
                contract_address=token_address,
                reasons=[f"Analysis failed; trade deferred: {str(e)}"],
            )
    
    async def _check_transfer_fee(self, token_address: str) -> bool:
        """Check if token has transfer fee extension.
        
        In production, this would:
        1. Fetch token account from Solana RPC
        2. Parse for transfer fee extension
        3. Return bool indicating if fee exists
        """
        # Token-2022 extension parsing can be added when a binary account
        # decoder is introduced; authority checks are already enforced.
        return False
    
    async def _check_mint_authority(self, token_address: str) -> Optional[str]:
        """Check if mint authority is active (not renounced).
        
        Returns:
        - None if mint authority is renounced
        - str (authority address) if active
        """
        mint_info = await self.rpc.get_mint(token_address)
        return mint_info.get("mint_authority") if mint_info else None
    
    async def _check_freeze_authority(self, token_address: str) -> Optional[str]:
        """Check if freeze authority exists.
        
        Returns:
        - None if no freeze authority
        - str (authority address) if exists
        """
        mint_info = await self.rpc.get_mint(token_address)
        return mint_info.get("freeze_authority") if mint_info else None
