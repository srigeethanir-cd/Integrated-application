"""Abstract base class for all AI BA Accelerator agents."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from agents.common.execution_manager import AgentExecutionManager
from agents.common.llm_factory import LLMClientAdapter, LLMFactory
from agents.common.prompt_loader import PromptLoader
from agents.common.response_parser import ResponseParser
from agents.common.state_manager import AgentStateManager

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract Base Agent defining lifecycle, LLM invocation, parsing, and error handling."""

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        llm: Optional[LLMClientAdapter] = None,
        prompt_loader: Optional[PromptLoader] = None,
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.llm = llm or LLMFactory.create_llm_client()
        self.prompt_loader = prompt_loader or PromptLoader()
        self.response_parser = ResponseParser()
        self.state_manager = AgentStateManager()
        self.execution_manager = AgentExecutionManager()
        self.logger = logging.getLogger(f"agents.{agent_id}")

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input payload before executing step logic."""
        pass

    @abstractmethod
    def format_prompt(self, input_data: Dict[str, Any]) -> str:
        """Construct formatted user prompt string for the LLM call."""
        pass

    def get_system_prompt(self) -> Optional[str]:
        """Return optional system prompt string."""
        return f"You are {self.agent_name}, an expert AI software architecture accelerator."

    def parse_response(self, raw_output: str) -> Dict[str, Any]:
        """Parse raw LLM response text into a structured dictionary."""
        return self.response_parser.extract_json(raw_output)

    def execute_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
    ) -> str:
        """Invoke LLM client generator with token limit safeguards."""
        sys_prompt = system_prompt or self.get_system_prompt()
        return self.llm.generate(
            prompt=prompt,
            system_prompt=sys_prompt,
            temperature=0.2,
            max_tokens=max_tokens,
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete agent step execution pipeline."""
        self.logger.info("[%s] Running agent process for input keys: %s", self.agent_id, list(input_data.keys()))

        if not self.validate_input(input_data):
            error_msg = f"[{self.agent_id}] Input validation failed for payload"
            self.logger.error(error_msg)
            self.state_manager.record_step(self.agent_name, "validate_input", "failed", error=error_msg)
            return {"success": False, "error": error_msg, "agent_id": self.agent_id}

        prompt = self.format_prompt(input_data)

        def _step():
            raw_response = self.execute_llm(prompt)
            parsed = self.parse_response(raw_response)
            return {"raw_response": raw_response, "parsed": parsed}

        exec_res = self.execution_manager.execute_with_retry(
            _step, step_name=f"{self.agent_id}_llm_step"
        )

        if not exec_res["success"]:
            self.state_manager.record_step(self.agent_name, "execute_llm", "failed", error=exec_res["error"])
            return {"success": False, "error": exec_res["error"], "agent_id": self.agent_id}

        output_data = exec_res["result"]["parsed"]
        self.state_manager.record_step(self.agent_name, "completed", "passed", output=output_data)

        return {
            "success": True,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "data": output_data,
            "metrics": {
                "attempts": exec_res["attempts"],
                "duration_seconds": exec_res["duration_seconds"],
            },
        }
