"""Data models for security check results."""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from decimal import Decimal


@dataclass
class SecurityCheckResult:
    """Base result class for all security checks."""
    is_blocked: bool
    block_reason: Optional[str] = None
    risk_score: int = 0  # 0-100
    reasons: List[str] = field(default_factory=list)
    details: Dict = field(default_factory=dict)

    @property
    def reason(self) -> str:
        """Return a non-empty reason for logs and callers."""
        return self.block_reason or (self.reasons[0] if self.reasons else "Security verification unavailable")


@dataclass
class LiquidityCheckResult(SecurityCheckResult):
    """Liquidity guard result."""
    liquidity_usd: Optional[Decimal] = None
    threshold_met: bool = False
    is_unknown: bool = False


@dataclass
class HoneypotCheckResult(SecurityCheckResult):
    """Honeypot detector result."""
    buy_count: int = 0
    sell_count: int = 0
    buy_sell_ratio: float = 0.0


@dataclass
class ContractAnalysisResult(SecurityCheckResult):
    """Contract analysis result."""
    contract_address: str = ""
    has_transfer_fee: bool = False
    mint_authority: Optional[str] = None
    freeze_authority: Optional[str] = None
    update_authority: Optional[str] = None
    suspicious_functions: List[str] = field(default_factory=list)
    known_honeypot: bool = False
    is_unknown: bool = False


@dataclass
class HolderAnalysisResult(SecurityCheckResult):
    """Holder distribution result."""
    top_10_pct: float = 0.0
    top_10_count: int = 0
    concentration_score: int = 0
    is_concentrated: bool = False
    excluded_lp_count: int = 0
    is_unknown: bool = False


@dataclass
class MetadataCheckResult(SecurityCheckResult):
    """Token metadata validation result."""
    name: Optional[str] = None
    symbol: Optional[str] = None
    spoofed_symbol: Optional[str] = None


@dataclass
class DeveloperCheckResult(SecurityCheckResult):
    """Developer wallet registry result."""
    developer_address: Optional[str] = None
    scam_count: int = 0


@dataclass
class SecurityGateResult:
    """Final result from SecurityGateService."""
    is_blocked: bool
    is_deferred: bool = False
    block_reason: Optional[str] = None
    security_gate_score: int = 0
    findings: Dict[str, SecurityCheckResult] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    passed_at: Optional[str] = None  # ISO timestamp

    @property
    def status(self) -> str:
        """Stable status for logs and API consumers."""
        if self.is_blocked:
            return "BLOCKED"
        if self.is_deferred:
            return "DEFERRED"
        return "PASSED"

    @property
    def reason(self) -> str:
        """Return a non-empty human-readable reason for non-passed results."""
        return self.block_reason or (self.reasons[0] if self.reasons else "Security verification unavailable")
