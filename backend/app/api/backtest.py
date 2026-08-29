from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.core.security import verify_token
from app.services.backtest.engine import BacktestEngine
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["backtest"], prefix="/backtest")


@router.post("/run")
async def run_backtest(
    pair_id: str,
    days: int = 30,
    initial_balance: float = 1000,
    payload: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_db_session),
):
    """Run backtest on a pair for specified number of days."""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        engine = BacktestEngine()
        metrics = await engine.backtest(
            session,
            pair_id=pair_id,
            start_date=start_date,
            end_date=end_date,
            initial_balance=__import__("decimal").Decimal(str(initial_balance)),
        )
        
        logger.info(f"Backtest completed for pair {pair_id}")
        return {
            "pair_id": pair_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "metrics": {
                "total_trades": metrics.total_trades,
                "winning_trades": metrics.winning_trades,
                "losing_trades": metrics.losing_trades,
                "win_rate": f"{metrics.win_rate:.2f}%",
                "total_pnl": f"${float(metrics.total_pnl):.2f}",
                "total_pnl_pct": f"{metrics.total_pnl_pct:.2f}%",
                "max_drawdown": f"{metrics.max_drawdown:.2f}%",
                "sharpe_ratio": f"{metrics.sharpe_ratio:.2f}",
                "avg_trade_pnl": f"${float(metrics.avg_trade_pnl):.2f}",
            },
        }
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=400, detail=str(e))
