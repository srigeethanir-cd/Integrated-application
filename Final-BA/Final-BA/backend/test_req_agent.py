import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.agents.requirement_analysis_agent import RequirementAnalysisAgent

async def main():
    agent = RequirementAnalysisAgent()
    try:
        # Pass a dummy chunk to trigger the LLM call
        res = await agent.run([{"text": "The system shall allow users to log in."}])
        print(res)
    except Exception as e:
        print("EXCEPTION:", e)

if __name__ == "__main__":
    asyncio.run(main())
