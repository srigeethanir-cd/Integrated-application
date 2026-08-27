import json, asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

async def run():
    engine = create_async_engine('postgresql+asyncpg://neondb_owner:npg_pZ0GlobxmfF2@ep-little-fire-aij5loa4-pooler.c-4.us-east-1.aws.neon.tech/neondb?ssl=require')
    session_maker = async_sessionmaker(engine)
    async with session_maker() as session:
        res = await session.execute(text('SELECT state_data FROM workflow_states ORDER BY created_at DESC LIMIT 1'))
        state = res.scalar()
        if state:
            stories = state.get('user_stories', [])
            print(json.dumps(stories[0] if stories else {}, indent=2))
        else:
            print("No state found")

asyncio.run(run())
