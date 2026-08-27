"""
API Analyzer for FCE.

Extracts HTTP fetch/axios calls, endpoints, HTTP verbs, error handling, and loading states.
"""

from typing import Any, Dict, List
from app.services.frontend_context.models import ApiCallContextItem


class ApiAnalyzer:
    """Extracts API and service call details."""

    def extract(self, comp_data: Dict[str, Any]) -> List[ApiCallContextItem]:
        api_calls: List[ApiCallContextItem] = []
        raw_api = comp_data.get("api_calls") or comp_data.get("services") or []

        for api in raw_api:
            if isinstance(api, dict):
                fn_name = api.get("function_name") or api.get("name") or "fetch"
                ep = api.get("endpoint") or api.get("url")
                method = api.get("http_method") or "GET"
                is_a = bool(api.get("is_async", True))
                has_err = bool(api.get("has_error_handling", False))
                in_eff = bool(api.get("in_use_effect", False))
                load_var = api.get("loading_state_var")

                api_calls.append(
                    ApiCallContextItem(
                        function_name=fn_name,
                        endpoint=str(ep) if ep is not None else None,
                        http_method=str(method),
                        is_async=is_a,
                        has_error_handling=has_err,
                        in_use_effect=in_eff,
                        loading_state_var=str(load_var) if load_var is not None else None,
                    )
                )

        return api_calls
