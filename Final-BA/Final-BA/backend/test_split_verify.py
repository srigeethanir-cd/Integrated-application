import os
os.environ['MODEL_PROVIDER'] = 'groq'
os.environ['MODEL_NAME'] = 'llama-3.1-8b-instant'
os.environ['REQUIREMENT_ANALYSIS_MAX_INPUT_TOKENS'] = '5000'
os.environ['REQUIREMENT_ANALYSIS_MAX_OUTPUT_TOKENS'] = '1500'

from app.agents.requirement_analysis_agent import RequirementAnalysisAgent
from app.prompts.prompt_manager import PromptManager
from app.agents.token_budget import count_tokens

agent = RequirementAnalysisAgent()
pm = PromptManager()
sys_prompt = pm.get_requirement_analysis_system_prompt()
sys_tokens, template_overhead = agent._get_fixed_overhead(sys_prompt)
max_out = 1500
safe_limit = 5000
available = safe_limit - sys_tokens - template_overhead - max_out

print(f"available_content = {available}")
print()

# Test 1: Very large single paragraph (no newlines)
print("=== TEST 1: Giant single paragraph ===")
content1 = "This is a requirement statement about login functionality and user management. " * 300
chunk1 = {'chunk_id': 'BRD-HUGE', 'chunk_index': 1, 'content': content1, 'context': 'requirement'}
ct1 = count_tokens(content1)
print(f"Content tokens: {ct1}")
batches1 = agent._build_batches([chunk1], available_content_tokens=available, system_prompt=sys_prompt)
all_fit1 = all(count_tokens(c.get('content','')) <= available for b in batches1 if isinstance(b, list) for c in b)
all_ref1 = all(c.get('chunk_id') == 'BRD-HUGE' for b in batches1 if isinstance(b, list) for c in b)
print(f"Batches: {len(batches1)} | All fit: {all_fit1} | chunk_refs preserved: {all_ref1}")
print()

# Test 2: Multiple chunks, some small, some large
print("=== TEST 2: Mixed sized chunks ===")
chunks2 = [
    {'chunk_id': 'C-001', 'chunk_index': 1, 'content': 'Short chunk about login.' * 5, 'context': 'requirement'},
    {'chunk_id': 'C-002', 'chunk_index': 2, 'content': 'Medium chunk. ' * 100, 'context': 'requirement'},
    {'chunk_id': 'C-003', 'chunk_index': 3, 'content': 'Huge chunk. ' * 1000, 'context': 'requirement'},
    {'chunk_id': 'C-004', 'chunk_index': 4, 'content': 'Another small chunk.' * 10, 'context': 'requirement'},
]
batches2 = agent._build_batches(chunks2, available_content_tokens=available, system_prompt=sys_prompt)
all_fit2 = all(count_tokens(c.get('content','')) <= available for b in batches2 if isinstance(b, list) for c in b)
chunk_ids_seen = set(c.get('chunk_id') for b in batches2 if isinstance(b, list) for c in b)
print(f"Batches: {len(batches2)} | All fit: {all_fit2} | IDs seen: {sorted(chunk_ids_seen)}")
print()

# Test 3: 413 retry splitting path
print("=== TEST 3: _split_batch_by_content ===")
huge_chunk = {'chunk_id': 'BRD-413', 'chunk_index': 99, 'content': 'A long sentence. ' * 400, 'context': 'requirement'}
batch_413 = [huge_chunk]
new_budget = available // 2
sub = agent._split_batch_by_content(batch_413, new_budget, sys_prompt)
all_fit3 = all(count_tokens(c.get('content','')) <= new_budget for sb in sub if isinstance(sb, list) for c in sb)
refs3 = all(c.get('chunk_id') == 'BRD-413' for sb in sub if isinstance(sb, list) for c in sb)
print(f"Sub-batches: {len(sub)} | All fit in new_budget ({new_budget}): {all_fit3} | chunk_refs preserved: {refs3}")
print()

print("ALL TESTS PASSED" if all_fit1 and all_ref1 and all_fit2 and all_fit3 and refs3 else "SOME TESTS FAILED")
