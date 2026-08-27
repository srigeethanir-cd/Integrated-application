"""
Failure Analysis Service – Diagnosis of real Jest test execution failures using traceability context.
"""

import logging
import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FailureAnalysisReport(BaseModel):
    """Structured failure analysis report produced post-test execution."""

    test_case_id: str = Field(..., description="Target test case ID.")
    component: str = Field(..., description="Target component name under test.")
    function: str = Field(..., description="Target function or event handler under test.")
    failure_reason: str = Field(..., description="Human-readable diagnosis of why the test failed.")
    mismatch_type: str = Field(..., description="Classification: SelectorMismatch, ExpectedValueMismatch, MockMissing, AsyncTimeout, SetupError.")
    expected: str = Field(..., description="Expected outcome from test assertion or specification.")
    actual: str = Field(..., description="Actual outcome returned during Jest execution.")
    error_message: str = Field(..., description="Raw Jest error message.")
    stack_trace: Optional[str] = Field(None, description="Full Jest stack trace.")
    source_context: str = Field(..., description="Relevant component source code snippet.")
    regeneration_recommended: bool = Field(True, description="True if targeted test regeneration is recommended.")
    suggested_fix: str = Field(..., description="Recommended technical adjustment for test regeneration.")


class FailureAnalysisService:
    """Diagnoses Jest execution failures against source code and traceability metadata."""

    def analyze_failure(
        self,
        test_case_id: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        expected: Optional[str] = None,
        actual: Optional[str] = None,
        traceability: Optional[Dict[str, Any]] = None,
        source_code: Optional[str] = None,
        test_file_code: Optional[str] = None,
    ) -> FailureAnalysisReport:
        """Analyze a Jest assertion failure and return a structured failure diagnosis."""
        trace = traceability or {}
        comp_name = trace.get("component", {}).get("name") if isinstance(trace.get("component"), dict) else (trace.get("component") or "Component")
        fn_name = trace.get("function_behavior") or trace.get("source_function") or "render()"

        err_msg = error_message or "Jest assertion failed"
        stack = stack_trace or ""

        # Default classification
        mismatch_type = "ExpectedValueMismatch"
        reason = "Expected outcome did not match actual execution state."
        fix = "Adjust expected assertion value to align with source component contract."

        # Detect Selector Mismatch
        if any(term in err_msg.lower() or term in stack.lower() for term in ["unable to find", "getBy", "findBy", "queryBy", "by.css", "element not found", "null is not an object"]):
            mismatch_type = "SelectorMismatch"
            reason = f"Target DOM element or selector mismatch in component '{comp_name}' for function '{fn_name}'."
            fix = "Update element query selector or role accessibility label to match component JSX/template structure."

        # Detect Unhandled Service / Mock Failure
        elif any(term in err_msg.lower() or term in stack.lower() for term in ["cannot read properties of undefined", "no provider for", "is not a function", "httpclient", "mock"]):
            mismatch_type = "MockMissing"
            reason = f"Missing dependency service injection or mock method for '{fn_name}'."
            fix = "Inject required mock service provider or stub HTTP backend response in test setup."

        # Detect Async / Timeout Failure
        elif any(term in err_msg.lower() or term in stack.lower() for term in ["exceeded timeout", "fakeasync", "periodictimer", "async", "promise"]):
            mismatch_type = "AsyncTimeout"
            reason = f"Asynchronous state update or timer unresolved during '{fn_name}' execution."
            fix = "Wrap test interaction in fakeAsync/tick() or waitFor() to flush asynchronous state updates."

        # Detect Expected Value Mismatch
        elif "expect(" in err_msg.lower() or "received" in err_msg.lower() or "expected" in err_msg.lower():
            mismatch_type = "ExpectedValueMismatch"
            # Extract expected vs actual from Jest error message if present
            exp_match = re.search(r"Expected:\s*(.*)", err_msg)
            rec_match = re.search(r"Received:\s*(.*)", err_msg)
            if exp_match and not expected:
                expected = exp_match.group(1).strip()
            if rec_match and not actual:
                actual = rec_match.group(1).strip()

            reason = f"Value assertion mismatch in function '{fn_name}'. Expected '{expected or 'valid state'}' but received '{actual or 'different value'}'."
            fix = "Update expected value or assertion comparison logic in regenerated test case."

        # Source context snippet
        ctx_snippet = ""
        if source_code:
            lines = source_code.splitlines()
            ctx_snippet = "\n".join(lines[:20])
        else:
            ctx_snippet = f"Component: {comp_name}\nFunction: {fn_name}\nTarget File: {trace.get('source_file', 'SourceFile.tsx')}"

        return FailureAnalysisReport(
            test_case_id=test_case_id,
            component=str(comp_name),
            function=str(fn_name),
            failure_reason=reason,
            mismatch_type=mismatch_type,
            expected=expected or "Expected component validation or state transition",
            actual=actual or "Execution state mismatch or element not found",
            error_message=err_msg,
            stack_trace=stack,
            source_context=ctx_snippet,
            regeneration_recommended=True,
            suggested_fix=fix,
        )
