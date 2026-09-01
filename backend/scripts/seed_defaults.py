"""Idempotently seed database defaults after migrations."""
import asyncio

from app.core.database import async_session_maker
from app.services import ChainService
from app.services.settings.service import SettingsService


async def main() -> None:
    async with async_session_maker() as session:
        await ChainService.create_or_get_chain(session, "solana")
        await SettingsService.get_or_create_bot_state(session)
        await SettingsService.seed_default_strategies(session)
        print("Database defaults are ready", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
