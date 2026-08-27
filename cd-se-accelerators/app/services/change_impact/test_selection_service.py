import logging
import os
from typing import Dict, List, Set, Optional, Any
from app.models.change_impact_models import RecommendedTestCase, TraceabilityStep, ChangeImpactResponse
from app.models.test_case_models import TestCase
from app.models.ir_models import FrameworkAgnosticIR

logger = logging.getLogger(__name__)


class TestSelectionService:
    """Bridges impact analyzer results with physical Jest test suites and files."""

    def select_tests(
        self,
        test_cases: List[TestCase],
        manifest: Dict[str, Any],
        impacted_components: Dict[str, str],
        impact_reasons: Dict[str, str],
        global_reasons: List[str],
        changed_files: List[str]
    ) -> ChangeImpactResponse:
        """Filter test cases and files based on impact propagation.

        Args:
            test_cases: List of TestCase models.
            manifest: Test manifest structure containing generated files information.
            impacted_components: Dict mapping component -> impact level.
            impact_reasons: Dict mapping component -> explanation.
            global_reasons: List of overall reasons.
            changed_files: User-provided changed files list.

        Returns:
            ChangeImpactResponse with full selection details.
        """
        total_tests = len(test_cases)
        
        # Build map from test_case_id to test_file path using manifest
        case_to_file: Dict[str, str] = {}
        for gen_file in manifest.get("generated_files", []):
            file_name = gen_file.get("file_name") or gen_file.get("file") or ""
            file_path = gen_file.get("file_path") or f"tests/react/{file_name}"
            for tc_id in gen_file.get("test_cases", []) or gen_file.get("test_case_ids", []):
                case_to_file[tc_id] = file_path

        recommended_tests: List[RecommendedTestCase] = []
        traceability_steps: List[TraceabilityStep] = []
        reasons_set: Set[str] = set(global_reasons)

        for tc in test_cases:
            comp_name = tc.component
            # If the component this test case tests is impacted
            if comp_name in impacted_components:
                level = impacted_components[comp_name]
                reason = impact_reasons.get(comp_name, f"Related component '{comp_name}' was modified")
                reasons_set.add(reason)
                
                # Retrieve associated test file
                test_file = case_to_file.get(tc.id) or case_to_file.get(tc.id.replace(f"{tc.project_id}_", "")) or f"tests/react/{comp_name}.test.jsx"
                
                # Determine which changed file caused this impact
                primary_changed_file = changed_files[0] if changed_files else "unknown"
                for cf in changed_files:
                    if comp_name.lower() in cf.lower():
                        primary_changed_file = cf
                        break

                # Create traceability step
                # Chain: Changed File → Component → IR Element/Event/State → Strategy → Edge Case → Test Case → Test File
                trace_step = TraceabilityStep(
                    changed_file=primary_changed_file,
                    component=comp_name,
                    ir_element=tc.target_function or tc.traceability.element_id if tc.traceability else "Component Render",
                    strategy=tc.strategy_id,
                    edge_case=tc.edge_case_id,
                    test_case_id=tc.id,
                    test_file=test_file
                )
                traceability_steps.append(trace_step)

                # Create recommended test case metadata
                recommended_tc = RecommendedTestCase(
                    test_case_id=tc.id,
                    title=tc.title,
                    component=comp_name,
                    category=tc.category or "General",
                    priority=tc.priority or "Medium",
                    impact_level=level,
                    reason=reason,
                    test_file=os.path.basename(test_file),
                    traceability=trace_step
                )
                recommended_tests.append(recommended_tc)

        impacted_tests_count = len(recommended_tests)
        unaffected_tests_count = max(0, total_tests - impacted_tests_count)
        
        # Calculate impact score
        impact_score = round((impacted_tests_count / total_tests * 100.0), 1) if total_tests > 0 else 0.0
        
        # Calculate estimated reduction percentage
        reduction_percent = round((unaffected_tests_count / total_tests * 100.0), 1) if total_tests > 0 else 0.0

        # Determine overall global impact level
        global_level = "LOW"
        if any(item.impact_level == "HIGH" for item in recommended_tests):
            global_level = "HIGH"
        elif any(item.impact_level == "MEDIUM" for item in recommended_tests):
            global_level = "MEDIUM"

        return ChangeImpactResponse(
            total_tests=total_tests,
            impacted_tests=impacted_tests_count,
            unaffected_tests=unaffected_tests_count,
            recommended_tests_count=impacted_tests_count,
            recommended_tests=recommended_tests,
            impact_score=impact_score,
            impact_level=global_level,
            reasons=sorted(list(reasons_set)),
            estimated_reduction_percent=reduction_percent,
            traceability=traceability_steps
        )
