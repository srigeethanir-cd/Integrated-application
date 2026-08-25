"""
Context Completeness Validator for FCE.

Validates extracted SingleComponentFrontendContext models and produces CompletenessReport metrics.
"""

import logging
from typing import List
from app.services.frontend_context.models import CompletenessReport, SingleComponentFrontendContext

logger = logging.getLogger(__name__)


class ContextValidator:
    """Validates extracted component contexts and generates completeness reports."""

    def validate_and_generate_report(
        self,
        contexts: List[SingleComponentFrontendContext],
        discovered_count: int,
    ) -> CompletenessReport:
        tot_fn = sum(len(c.functions) for c in contexts)
        tot_st = sum(len(c.states) for c in contexts)
        tot_hk = sum(len(c.hooks) for c in contexts)
        tot_hand = sum(len(c.events) for c in contexts)
        tot_api = sum(len(c.api_calls) for c in contexts)
        tot_val = sum(len(c.validations) for c in contexts)

        incomplete: List[str] = []
        for c in contexts:
            # Check if component has no states, functions, or props
            if not c.states and not c.functions and not c.props and not c.events:
                incomplete.append(c.component_id)

        report = CompletenessReport(
            components_discovered=max(discovered_count, len(contexts)),
            components_analyzed=len(contexts),
            functions_discovered=tot_fn,
            states_discovered=tot_st,
            hooks_discovered=tot_hk,
            handlers_discovered=tot_hand,
            api_calls_discovered=tot_api,
            validations_discovered=tot_val,
            incomplete_contexts=incomplete,
        )

        logger.info(
            "FCE Completeness Validation Summary:\n"
            "  components_discovered: %d\n"
            "  components_analyzed: %d\n"
            "  functions_discovered: %d\n"
            "  states_discovered: %d\n"
            "  hooks_discovered: %d\n"
            "  handlers_discovered: %d\n"
            "  api_calls_discovered: %d\n"
            "  validations_discovered: %d\n"
            "  incomplete_contexts: %d",
            report.components_discovered,
            report.components_analyzed,
            report.functions_discovered,
            report.states_discovered,
            report.hooks_discovered,
            report.handlers_discovered,
            report.api_calls_discovered,
            report.validations_discovered,
            len(report.incomplete_contexts),
        )

        return report
