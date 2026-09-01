import asyncio
from app.database.connection import async_session_maker
from app.database.models import WorkflowStateModel
from sqlalchemy import delete

async def main():
    async with async_session_maker() as session:
        await session.execute(delete(WorkflowStateModel))
        await session.commit()
        print("Successfully cleared cached failed workflow states from Database!")

if __name__ == "__main__":
    asyncio.run(main())
