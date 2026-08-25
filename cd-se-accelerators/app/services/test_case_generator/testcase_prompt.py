"""
TestCase Generator Prompt Specification – Module 7 Groq LLM Integration.

Defines the system prompt and dynamic prompt builder for generating executable test-case
specifications from IR, Test Strategy, and Edge Case inputs.
"""

SYSTEM_PROMPT = """You are a frontend unit-test design engine.

Generate high-quality, executable test-case specifications from the provided:
1. Intermediate Representation (IR)
2. Test Strategy
3. Edge Case

GOAL:
Create meaningful frontend unit tests that can later be converted into Jest + React Testing Library or Jest + Angular TestBed code.

RULES:
- Use only information present in the supplied IR, strategy, and edge case.
- Do not invent components, elements, events, states, props, APIs, routes, or expected behavior.
- Each test must validate one specific behavior.
- Prefer observable UI/state behavior over implementation details.
- Convert the edge case into a concrete test scenario.
- Use actual component names and available UI elements.
- Use actual locators from the IR when available.
- Include realistic test data when the IR supports it.
- Every action must have a concrete expected outcome.
- Avoid generic phrases such as "perform action", "verify target", or "appropriate behavior".
- Do not include cleanup/unmount steps unless behaviorally relevant.
- Avoid duplicate test cases.
- Preserve strategy_id, edge_case_id, component_id, element_id, event_id, and state_id for traceability.
- If the provided information is insufficient, mark the test as insufficient_test_information instead of hallucinating.

TEST CASE MUST CONTAIN:
- id
- title
- objective
- component
- category
- priority
- preconditions
- test_data
- steps
- expected_result
- traceability

STEP FORMAT:
Each step must contain:
- action
- expected

QUALITY REQUIREMENTS:
- Test should be understandable to a developer or QA tester.
- Test should be directly convertible into executable Jest/RTL or Jest/TestBed code.
- Expected results must be observable and verifiable.
- The generated test must correspond directly to its strategy and edge case.
- Do not expose raw internal IDs in title, objective, steps, or expected result.

Return ONLY valid JSON matching the provided Pydantic schema.
Do not return markdown.
Do not return explanations."""


def build_testcase_prompt(
    ir_summary: str,
    strategy_info: str,
    edge_case_info: str,
    target_component: str,
) -> str:
    """Build dynamic user prompt containing IR, Strategy, and Edge Case context."""
    return f"""Generate a high-quality frontend unit-test specification for target component '{target_component}'.

1. INTERMEDIATE REPRESENTATION (IR):
{ir_summary}

2. TEST STRATEGY:
{strategy_info}

3. EDGE CASE SCENARIO:
{edge_case_info}

Return a strictly formatted JSON object with the following schema:
{{
  "id": "TC-<strategy_id>-<edge_case_id>",
  "title": "Clear human-readable test title without raw IDs",
  "objective": "Detailed objective of what is verified",
  "component": "{target_component}",
  "category": "State|Events|Forms|Services|Routing|Accessibility",
  "priority": "High|Medium|Low",
  "preconditions": ["Precondition step 1"],
  "test_data": {{"key": "value"}},
  "steps": [
    {{"action": "Mount component and set up initial props", "expected": "Component renders cleanly in DOM"}},
    {{"action": "User interacts with target UI element", "expected": "State or UI updates as specified"}}
  ],
  "expected_result": "Concrete observable expected outcome",
  "element_locator": {{"strategy": "role|label|test-id|text", "value": "element-name"}},
  "action": "click|type|render|select|submit",
  "assertion_type": "exists|visible|equals|contains|called",
  "insufficient_test_information": false
}}
"""
