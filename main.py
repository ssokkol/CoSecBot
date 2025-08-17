import asyncio
from src.bot import DiscordBot

async def main():
    bot = DiscordBot()
    await bot.run_bot()

if __name__ == "__main__":
    asyncio.run(main())
