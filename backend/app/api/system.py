from fastapi import APIRouter, Depends
from app.core.security import verify_token
from app.core.config import settings
from app.services.prediction.engine import PredictionEngine
from app.services.wallet.service import WalletService
from app.adapters.blockchain import SolanaJupiterAdapter

router = APIRouter(tags=["system"], prefix="/system")


@router.get("/status")
async def get_system_status(payload: dict = Depends(verify_token)):
    """Integration health: Jupiter, ML model, wallet."""
    adapter = SolanaJupiterAdapter()
    jupiter_healthy = False
    try:
        jupiter_healthy = await adapter.is_healthy()
    except Exception:
        pass

    return {
        "environment": settings.ENVIRONMENT,
        "trading_mode": settings.TRADING_MODE,
        "paper_initial_balance": settings.PAPER_INITIAL_BALANCE,
        "integrations": {
            "jupiter_api": {
                "url": settings.JUPITER_API_URL,
                "solana_rpc": settings.SOLANA_RPC_URL,
                "rpc_healthy": jupiter_healthy,
            },
            "ml_model": {
                "available": PredictionEngine.is_available(),
                "path": str(settings.ML_MODEL_PATH),
                "threshold": settings.ML_PREDICTION_THRESHOLD,
            },
            "wallet": {
                "configured": WalletService.is_configured(),
                "address": WalletService.get_address(),
            },
        },
        "limits": {
            "max_live_trade_usd": settings.MAX_LIVE_TRADE_USD,
            "default_slippage_bps": settings.DEFAULT_SLIPPAGE_BPS,
        },
    }
