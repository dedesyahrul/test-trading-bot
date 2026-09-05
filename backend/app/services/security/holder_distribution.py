"""Holder distribution analyzer for detecting concentrated ownership."""

import logging
from typing import List, Dict
from app.services.security.models import HolderAnalysisResult
from app.adapters.solana_rpc import SolanaRPCClient
from app.core.config import settings

logger = logging.getLogger(__name__)

# Known LP and burn addresses to exclude from concentration analysis
KNOWN_LP_ADDRESSES = {
    # Raydium LP
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1xF",
    # Orca LP
    "9W957wfaHHNaG9eZyEmu4r34Marj4KXQxupT8PGkxbreak",
    # Magic Eden
    "1BWutmtRyPHTu1JeuknkQv4FVsihgg6ein6qBUR5alaW",
    # Burn address
    "1111111111111111111111111111111111111111111111",
    # System program
    "11111111111111111111111111111111",
}


class HolderDistributionAnalyzer:
    """Analyze top token holder concentration.
    
    Detects rugpull risk by identifying when a small number of wallets
    control a majority of the token supply. Excludes known LP and burn addresses.
    """
    
    CONCENTRATION_THRESHOLD = settings.SECURITY_HOLDER_CONCENTRATION_THRESHOLD

    def __init__(self, rpc_client: SolanaRPCClient | None = None):
        self.rpc = rpc_client or SolanaRPCClient()
    
    async def analyze(
        self,
        chain: str,
        token_address: str,
        top_n: int = 20,
    ) -> HolderAnalysisResult:
        """
        Analyze top token holders for concentration.
        
        Args:
            chain: "solana"
            token_address: Token mint address
            top_n: Number of top holders to analyze
        
        Returns:
            HolderAnalysisResult
        """
        try:
            # Step 1: Get total supply
            total_supply = await self._get_total_supply(token_address)
            
            if total_supply == 0:
                logger.error(f"Holder analysis FAILED: Zero total supply for {token_address}")
                return HolderAnalysisResult(
                    is_blocked=True,
                    block_reason="Zero total supply (invalid token)",
                    risk_score=100,
                    reasons=["Total supply is 0"],
                )
            
            # Step 2: Get top holders
            holders = await self._get_top_holders(token_address, top_n)
            if not holders:
                logger.warning(f"Could not fetch holder data for {token_address}")
                return HolderAnalysisResult(
                    is_blocked=False,
                    is_unknown=True,
                    risk_score=100,
                    reasons=["Critical holder data unavailable; trade deferred"],
                )
            
            # Step 3: Filter out LP and burn addresses
            non_lp_holders = [
                h for h in holders
                if h['address'] not in KNOWN_LP_ADDRESSES
            ]
            
            # Step 4: Calculate concentration
            top_10_pct = self._calculate_top_n_percentage(
                non_lp_holders[:10],
                total_supply
            )
            
            # Step 5: Determine concentration risk
            concentration_score = self._calculate_concentration_score(top_10_pct)
            is_concentrated = top_10_pct > self.CONCENTRATION_THRESHOLD
            
            risk_score = concentration_score
            reasons = [f"Top 10 holders: {top_10_pct:.1f}% of supply"]
            
            if is_concentrated:
                logger.error(f"CONCENTRATED HOLDERS DETECTED: {top_10_pct:.1f}% in top 10 - BLOCKING")
                reasons.append(f"CONCENTRATED: {top_10_pct:.1f}% > {self.CONCENTRATION_THRESHOLD}% threshold")
            else:
                logger.info(f"Holder analysis OK: {top_10_pct:.1f}% in top 10 (score: {risk_score})")
            
            return HolderAnalysisResult(
                is_blocked=is_concentrated,
                block_reason=f"Holder concentration: {top_10_pct:.1f}% in top 10" if is_concentrated else None,
                risk_score=risk_score,
                top_10_pct=top_10_pct,
                top_10_count=len(non_lp_holders[:10]),
                concentration_score=concentration_score,
                is_concentrated=is_concentrated,
                excluded_lp_count=len(holders) - len(non_lp_holders),
                reasons=reasons,
                details={
                    'top_10_pct': top_10_pct,
                    'top_10_count': len(non_lp_holders[:10]),
                    'total_holders': len(holders),
                    'excluded_lp': len(holders) - len(non_lp_holders),
                }
            )
        
        except Exception as e:
            logger.error(f"Holder analysis error: {e}")
            return HolderAnalysisResult(
                is_blocked=False,
                is_unknown=True,
                risk_score=100,
                reasons=[f"Analysis failed; trade deferred: {str(e)}"],
            )
    
    async def _get_total_supply(self, token_address: str) -> float:
        """Get token total supply.
        
        Uses the normalized RPC adapter so tests and alternate providers can
        replace the adapter without changing this analyzer.
        """
        mint_info = await self.rpc.get_mint(token_address)
        return float((mint_info or {}).get("supply") or 0)
    
    async def _get_top_holders(self, token_address: str, top_n: int) -> List[Dict]:
        """Get top N token holders.
        
        Returns:
        [
            {'address': 'wallet_address', 'balance': 1000000},
            ...
        ]
        
        Returns owner wallets rather than token-account addresses.
        """
        return await self.rpc.get_top_holders(token_address, top_n)
    
    def _calculate_top_n_percentage(self, holders: List[Dict], total_supply: float) -> float:
        """Calculate % of supply held by top N holders."""
        if not holders or total_supply == 0:
            return 0.0
        
        top_n_balance = sum(float(h.get('balance') or 0) for h in holders)
        return (top_n_balance / total_supply) * 100
    
    def _calculate_concentration_score(self, top_10_pct: float) -> int:
        """
        Convert top 10 % to risk score (0-100).
        
        > 85% → 95 (block)
        70-85% → 80 (high risk)
        50-70% → 60 (medium)
        < 50% → 10-20 (safe)
        """
        if top_10_pct > 85:
            return 95
        elif top_10_pct > 70:
            return 80
        elif top_10_pct > 50:
            return 60
        elif top_10_pct > 30:
            return 35
        else:
            return 10
