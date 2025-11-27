import asyncio
import os
from dotenv import load_dotenv

from agents import Runner, set_default_openai_key
from custom_agents.scraper import scraper
from tools.browser.controller import close_browser


async def main():
    load_dotenv()
    set_default_openai_key(os.getenv("OPENAI_API_KEY"))

    print("🚀 Agente autónomo iniciado...\n")
    # objetivo = input("🎯 Objetivo del agente: ")
    objetivo = "Segmento 1, fecha más reciente"
    print(f"🎯 Objetivo: {objetivo}")

    result = await Runner.run(
        starting_agent=scraper,
        input=objetivo,
        max_turns=40,
    )

    print("\n" + "=" * 70)
    print(result.final_output)

    await close_browser()


if __name__ == "__main__":
    asyncio.run(main())
