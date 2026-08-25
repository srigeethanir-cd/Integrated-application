"""Detect application lifecycle behavior represented in Stage 3 artifacts."""

from __future__ import annotations

import re
from typing import Any

from app.schemas.test_case import TestCase


class LifecycleDetector:
    """Find concrete lifecycle patterns without inferring them for every project."""

    _patterns = {
        "startup_event": (
            r"\blifespan\b",
            r"\bon[_ -]?event\b.*\bstartup\b",
            r"\bstartup (?:event|hook|handler)\b",
            r"\bbefore[_ -]?serving\b",
        ),
        "application_initialization": (
            r"\bcreate[_ ]app\b",
            r"\b(?:initialize|initialise) (?:the )?(?:app|application)\b",
            r"\bapplication factory\b",
            r"\bfastapi application\b",
            r"\basgi application\b",
        ),
        "router_registration": (
            r"\binclude[_ ]router\b",
            r"\bregister (?:the )?(?:api )?router",
            r"\brouter registration\b",
            r"\bregister[_ ]blueprint\b",
        ),
        "dependency_initialization": (
            r"\bdependency initialization\b",
            r"\b(?:initialize|initialise) dependencies\b",
            r"\bdependency container\b",
            r"\bdependency injection (?:setup|startup|initialization)\b",
        ),
        "database_service_startup": (
            r"\b(?:database|redis|cache) (?:connection|startup|initialization)\b",
            r"\bconnect (?:to )?(?:the )?database\b",
            r"\bcreate (?:database )?tables\b",
            r"\b(?:start|initialize|initialise) (?:the )?[\w-]+ service\b",
            r"\bservice startup\b",
        ),
    }
    _artifact_collections = (
        "entrypoints",
        "components",
        "business_rules",
        "execution_flows",
        "test_targets",
        "analyzed_files",
    )
    _case_patterns = {
        "startup_event": (r"\bstartup\b", r"\blifespan\b"),
        "application_initialization": (
            r"\bapplication initialization\b",
            r"\b(?:initialize|initialise)s? (?:the )?(?:app|application)\b",
            r"\bapplication factory\b",
        ),
        "router_registration": (
            r"\brouter registration\b",
            r"\bregisters? (?:the )?(?:api )?routers?\b",
            r"\binclude[_ ]router\b",
        ),
        "dependency_initialization": (
            r"\bdependency initialization\b",
            r"\b(?:initialize|initialise)s? dependencies\b",
        ),
        "database_service_startup": (
            r"\b(?:database|service|redis|cache) startup\b",
            r"\b(?:initialize|initialise)s? (?:the )?database\b",
            r"\bconnects? (?:to )?(?:the )?database\b",
        ),
    }

    def detect(self, stage3_payload: dict[str, Any]) -> list[dict[str, Any]]:
        behaviors = []
        seen = set()
        for collection in self._artifact_collections:
            for artifact in stage3_payload.get(collection, []):
                if not isinstance(artifact, dict):
                    continue
                text = self._flatten(artifact)
                for behavior_type, patterns in self._patterns.items():
                    if not any(
                        re.search(pattern, text, re.IGNORECASE) for pattern in patterns
                    ):
                        continue
                    reference = {
                        "type": behavior_type,
                        "artifact": collection,
                        "file": artifact.get("file") or artifact.get("path"),
                        "symbol": artifact.get("symbol") or artifact.get("entrypoint"),
                        "evidence": self._evidence(artifact),
                    }
                    key = (
                        reference["type"],
                        reference["file"],
                        reference["symbol"],
                        reference["evidence"],
                    )
                    if key not in seen:
                        seen.add(key)
                        behaviors.append(
                            {key: value for key, value in reference.items() if value}
                        )
        return behaviors

    def filter_supported(
        self,
        test_cases: list[TestCase],
        behaviors: list[dict[str, Any]],
    ) -> list[TestCase]:
        """Remove lifecycle tests whose behavior has no Stage 3 evidence."""
        supported = {item["type"] for item in behaviors}
        filtered = []
        for case in test_cases:
            text = " ".join([case.title, case.description, *case.steps]).replace(
                "_", " "
            )
            referenced = {
                behavior_type
                for behavior_type, patterns in self._case_patterns.items()
                if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
            }
            if not referenced or referenced <= supported:
                filtered.append(case)
        return filtered

    @staticmethod
    def _flatten(value: Any) -> str:
        if isinstance(value, dict):
            return " ".join(LifecycleDetector._flatten(item) for item in value.values())
        if isinstance(value, list):
            return " ".join(LifecycleDetector._flatten(item) for item in value)
        return str(value or "").replace("_", " ")

    @staticmethod
    def _evidence(artifact: dict[str, Any]) -> str:
        for key in ("purpose", "name", "behavior", "description", "entrypoint"):
            value = artifact.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return LifecycleDetector._flatten(artifact)[:300]
