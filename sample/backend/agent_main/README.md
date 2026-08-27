# Agent Main

Unified agents, prompts, and LangGraph workflow orchestration module for the AI Business Analyst Accelerator.

## Subfolder Structure:
- `agents/`: Multi-agent pipeline definitions:
  - `agent0_wireframe/`: Wireframe vision extraction and UI component mapping.
  - `agent1_blueprint/`: System Architecture and Master Blueprint generation.
  - `agent2_story_generator/`: Sandboxed user story code generation.
  - `agent3_merge_validation/`: AST conflict resolution, story merge, and integration testing.
- `langgraph/`: LangGraph state machine definitions (workflow, nodes, edges, state).
- `prompts/`: System prompt templates for Agent 0, 1, 2, and 3.
- `orchestration/`: Multi-story dependency resolution and execution scheduling.
