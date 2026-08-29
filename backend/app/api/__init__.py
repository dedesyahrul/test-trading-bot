from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.market import router as market_router
from app.api.bot import router as bot_router
from app.api.backtest import router as backtest_router
from app.api.portfolio import router as portfolio_router

router = APIRouter()

# Include routers
router.include_router(auth_router)
router.include_router(market_router)
router.include_router(bot_router)
router.include_router(backtest_router)
router.include_router(portfolio_router)

# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
