import asyncio
import json
from asyncpg import connect

async def main():
    conn = await connect("postgresql://postgres:postgres@postgres:5432/cd_se_accelerators")
    row = await conn.fetchrow("""
        SELECT state_data::jsonb->'user_stories' 
        FROM workflow_states 
        WHERE workflow_id = 'heyy-broooo' 
          AND jsonb_typeof(state_data::jsonb->'user_stories') = 'array' 
        ORDER BY created_at DESC LIMIT 1;
    """)
    if row and row[0]:
        stories = json.loads(row[0])
        print(f"Total stories in workflow run: {len(stories)}")
        for i, s in enumerate(stories):
            ac_count = len(s.get("acceptance_criteria", []))
            br_count = len(s.get("business_rules", []))
            desc = s.get("description", "")
            print(f"Story #{i+1} ID={s.get('id')} Title='{s.get('title')}' ACs={ac_count} BRs={br_count} DescLen={len(desc)}")
            if ac_count == 0 or len(desc) == 0 or br_count == 0:
                print("  INCOMPLETE STORY DETAILED KEYS:")
                print("  acceptance_criteria:", s.get("acceptance_criteria"))
                print("  business_rules:", s.get("business_rules"))
                print("  description:", s.get("description"))
                print("  one_line_story_id:", s.get("one_line_story_id"))
                print("  chunk_ids_used:", s.get("chunk_ids_used"))
                print("---")
    await conn.close()

asyncio.run(main())
