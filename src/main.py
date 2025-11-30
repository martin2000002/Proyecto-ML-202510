import asyncio
import os
from dotenv import load_dotenv
from agents import Runner, set_default_openai_key
from custom_agents.scraper import scraper
from custom_agents.consolidator.orchestrator import consolidatorOrchestrator
from tools.browser.controller import close_browser


async def main():
    load_dotenv()
    set_default_openai_key(os.getenv("OPENAI_API_KEY"))

    print("🚀 Agente autónomo iniciado...\n")
    objetivo = "Segmento 1, fecha más reciente"
    print(f"🎯 Objetivo: {objetivo}")

    skip_scraper = False

    if not skip_scraper:
        result_scraper = await Runner.run(
            starting_agent=scraper,
            input=objetivo,
            max_turns=40,
        )
        print(f"🏁 Resultado Scraper: {result_scraper.final_output}")

        await close_browser()
    else:
         print("⏭️ Saltando Scraper...")

    result_consolidator = await Runner.run(
        starting_agent=consolidatorOrchestrator,
        input=f"Objetivo original: {objetivo}. Por favor consolida la información descargada.",
        max_turns=40,
    )
    print(f"🏁 Resultado Consolidator: {result_consolidator.final_output}")



if __name__ == "__main__":
    asyncio.run(main())
