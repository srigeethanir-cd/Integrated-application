"""Stage 3 agent for producing structured code-understanding results."""

from __future__ import annotations

import ast
import builtins
import json
import logging
import keyword as py_keyword
import re
import sys
import uuid
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.test_case import TestGenerationResult
from app.schemas.test_verification import TestVerificationResult
from app.schemas.test_quality import QualityEvaluation, QualityLoopResult
from app.schemas.runtime_preparation import RuntimeExecutionPlan

logger = logging.getLogger(__name__)


class _ExecutableNodeCollector(ast.NodeVisitor):
    """Collect direct runtime AST while excluding nested definitions/metadata."""

    def __init__(self) -> None:
        self.nodes: list[ast.AST] = []

    def visit(self, node: ast.AST) -> Any:
        self.nodes.append(node)
        return super().visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self.visit(node.value)


class SourceFileContext(BaseModel):
    """Bounded source content and Stage 2 metadata for one project file."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(description="Project-relative source path")
    language: str
    is_entry_point: bool = False
    imports: list[str] = Field(default_factory=list)
    classes: list[str] = Field(default_factory=list)
    functions: list[str] = Field(default_factory=list)
    content: str
    content_truncated: bool = False


class CodeUnderstandingContext(BaseModel):
    """Validated input assembled from a completed Stage 2 run."""

    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID
    dependency_run_id: uuid.UUID
    files: list[SourceFileContext]
    omitted_files: list[str] = Field(default_factory=list)
    security_findings: list[dict[str, Any]] = Field(default_factory=list)


class SecurityFindingDescription(BaseModel):
    """Semgrep finding attached to a Stage 3 source entity."""

    model_config = ConfigDict(extra="forbid")

    id: str
    rule_id: str
    severity: str
    file: str
    line: int
    message: str
    cwe: list[str] = Field(default_factory=list)
    owasp: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModuleDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    file: str
    imports: list[str] = Field(default_factory=list)
    runtime_resolvable: bool = True


class ImportDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module: str
    file: str
    names: list[str] = Field(default_factory=list)
    level: int = 0


class SymbolDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    qualified_name: str
    kind: str
    file: str
    line: int
    end_line: int
    parent: str | None = None


class CallGraphEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    caller: str
    callee: str
    file: str
    line: int


class FunctionDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    qualified_name: str
    module: str = ""
    owner_class: str | None = None
    file: str
    line: int
    end_line: int
    is_async: bool = False
    parameters: list[str] = Field(default_factory=list)
    return_type: str | None = None
    decorators: list[str] = Field(default_factory=list)
    calls: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    sqlalchemy_model_usage: list[str] = Field(default_factory=list)
    side_effects: list[str] = Field(default_factory=list)
    target_classification: str = "function"
    target_priority: str = "normal"
    runtime_resolvable: bool = True
    security_findings: list[SecurityFindingDescription] = Field(
        default_factory=list
    )


class ClassDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    qualified_name: str
    module: str = ""
    file: str
    line: int
    end_line: int
    fields: list[str] = Field(default_factory=list)
    bases: list[str] = Field(default_factory=list)
    inheritance: list[str] = Field(default_factory=list)
    decorators: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    sqlalchemy_model_usage: list[str] = Field(default_factory=list)
    constructor_dependencies: list[str] = Field(default_factory=list)
    target_classification: str = "class"
    target_priority: str = "normal"
    runtime_resolvable: bool = True
    security_findings: list[SecurityFindingDescription] = Field(
        default_factory=list
    )


class ArchitectureComponent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    responsibility: str
    files: list[str]
    dependencies: list[str] = Field(default_factory=list)


class EntrypointDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    symbol: str | None = None
    purpose: str


class ApiEndpointDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str
    route: str
    handler: str | None = None
    file: str
    request_type: str | None = None
    response_type: str | None = None
    request_model: str | None = None
    response_model: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    success_status_codes: list[int] = Field(default_factory=list)
    error_status_codes: list[int] = Field(default_factory=list)
    exception_status_mappings: list["ExceptionStatusMapping"] = Field(
        default_factory=list
    )
    authentication: str | None = None
    side_effects: list[str] = Field(default_factory=list)
    security_findings: list[SecurityFindingDescription] = Field(
        default_factory=list
    )


class ExceptionStatusMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exception: str
    status_code: int


class PydanticFieldDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: str
    required: bool
    optional: bool = False
    has_default: bool = False
    default: Any | None = None
    examples: list[Any] = Field(default_factory=list)
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    regex: str | None = None
    gt: Any | None = None
    lt: Any | None = None
    ge: Any | None = None
    le: Any | None = None
    description: str | None = None
    title: str | None = None
    default_factory: str | None = None


class PydanticValidatorDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    fields: list[str] = Field(default_factory=list)
    mode: str | None = None
    decorator: str
    is_async: bool = False


class PydanticSchemaDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    file: str
    fields: list[PydanticFieldDescription] = Field(default_factory=list)
    validators: list[PydanticValidatorDescription] = Field(default_factory=list)
    examples: list[Any] = Field(default_factory=list)


class SQLAlchemyColumnDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: str | None = None
    primary_key: bool = False
    foreign_keys: list[str] = Field(default_factory=list)
    nullable: bool | None = None
    default: Any | None = None
    index: bool = False
    unique: bool = False


class SQLAlchemySessionFactoryDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    file: str
    factory: str
    bind: str | None = None


class DataModelDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    file: str
    fields: list[str] = Field(default_factory=list)
    columns: list[SQLAlchemyColumnDescription] = Field(default_factory=list)
    primary_keys: list[str] = Field(default_factory=list)
    foreign_keys: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    indexes: list[str] = Field(default_factory=list)
    unique_constraints: list[str] = Field(default_factory=list)
    check_constraints: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    decorators: list[str] = Field(default_factory=list)
    sqlalchemy_model_usage: list[str] = Field(default_factory=list)
    security_findings: list[SecurityFindingDescription] = Field(
        default_factory=list
    )


class BusinessRuleDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    files: list[str]
    symbols: list[str] = Field(default_factory=list)


class ExecutionFlowDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    entrypoint: str
    steps: list[str]
    components: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)


class TestTargetDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    file: str
    line: int | None = None
    end_line: int | None = None
    qualified_name: str = ""
    module: str = ""
    owner_class: str | None = None
    target_classification: str = "function"
    target_priority: str = "normal"
    is_primary: bool = True
    runtime_resolvable: bool = True
    delegated_targets: list[str] = Field(default_factory=list)
    behavior: str
    dependencies: list[str] = Field(default_factory=list)
    side_effects: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    edge_cases: list[str] = Field(default_factory=list)
    branches: list[str] = Field(
        default_factory=list,
        description="Conditional outcomes that require independent test coverage",
    )
    security_findings: list[SecurityFindingDescription] = Field(
        default_factory=list
    )


class AmbiguityDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    files: list[str] = Field(default_factory=list)
    reason: str


class AnalyzedFileDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    purpose: str
    key_symbols: list[str] = Field(default_factory=list)


class RepositoryBehaviorContext(BaseModel):
    """Framework-neutral Stage 3 contract consumed by unit-test stages."""

    model_config = ConfigDict(extra="forbid")

    modules: list[ModuleDescription] = Field(default_factory=list)
    functions: list[FunctionDescription] = Field(default_factory=list)
    classes: list[ClassDescription] = Field(default_factory=list)
    call_graph: list[CallGraphEdge] = Field(default_factory=list)
    dependency_graph: list[dict[str, str]] = Field(default_factory=list)
    side_effects: dict[str, list[str]] = Field(default_factory=dict)
    exceptions: dict[str, list[str]] = Field(default_factory=dict)
    business_rules: list[BusinessRuleDescription] = Field(default_factory=list)


class CodeUnderstandingResult(BaseModel):
    """Structured Stage 3 artifact consumed by the Test Generation Agent."""

    model_config = ConfigDict(extra="forbid")

    project_summary: str
    architecture: str
    modules: list[ModuleDescription] = Field(default_factory=list)
    imports: list[ImportDescription] = Field(default_factory=list)
    functions: list[FunctionDescription] = Field(default_factory=list)
    classes: list[ClassDescription] = Field(default_factory=list)
    symbol_table: list[SymbolDescription] = Field(default_factory=list)
    call_graph: list[CallGraphEdge] = Field(default_factory=list)
    sqlalchemy_session_factories: list[
        SQLAlchemySessionFactoryDescription
    ] = Field(default_factory=list)
    security_findings: list[SecurityFindingDescription] = Field(
        default_factory=list
    )
    components: list[ArchitectureComponent] = Field(default_factory=list)
    entrypoints: list[EntrypointDescription] = Field(default_factory=list)
    api_endpoints: list[ApiEndpointDescription] = Field(default_factory=list)
    data_models: list[DataModelDescription] = Field(default_factory=list)
    pydantic_schemas: list[PydanticSchemaDescription] = Field(
        default_factory=list
    )
    business_rules: list[BusinessRuleDescription] = Field(default_factory=list)
    execution_flows: list[ExecutionFlowDescription] = Field(default_factory=list)
    external_dependencies: list[str] = Field(default_factory=list)
    test_targets: list[TestTargetDescription] = Field(default_factory=list)
    ambiguities: list[AmbiguityDescription] = Field(default_factory=list)
    analyzed_files: list[AnalyzedFileDescription] = Field(default_factory=list)
    repository_behavior: RepositoryBehaviorContext | None = None
    artifact_versions: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict,
        description="Immutable snapshots of regenerated downstream artifacts",
    )

    def assert_no_ellipsis(self) -> None:
        """Fail with an actionable path before JSON serialization."""

        def visit(
            value: Any,
            path: str,
            *,
            field_name: str,
            model_name: str,
        ) -> None:
            if value is Ellipsis:
                raise ValueError(
                    "Stage 3 contains non-serializable Ellipsis: "
                    f"field='{field_name}', path='{path}', "
                    f"offending_model='{model_name}'"
                )
            if isinstance(value, BaseModel):
                nested_model = type(value).__name__
                for nested_field in type(value).model_fields:
                    visit(
                        getattr(value, nested_field),
                        f"{path}.{nested_field}",
                        field_name=nested_field,
                        model_name=nested_model,
                    )
                return
            if isinstance(value, dict):
                for key, item in value.items():
                    visit(
                        item,
                        f"{path}[{key!r}]",
                        field_name=str(key),
                        model_name=model_name,
                    )
                return
            if isinstance(value, (list, tuple, set, frozenset)):
                for index, item in enumerate(value):
                    visit(
                        item,
                        f"{path}[{index}]",
                        field_name=field_name,
                        model_name=model_name,
                    )

        visit(
            self,
            type(self).__name__,
            field_name="<root>",
            model_name=type(self).__name__,
        )


class ProviderSemanticFlow(BaseModel):
    """Path-free semantic flow reasoning returned by the provider."""

    model_config = ConfigDict(extra="forbid")

    name: str
    steps: list[str] = Field(default_factory=list)


class ProviderSemanticAmbiguity(BaseModel):
    """Uncertainty that cannot be established by syntax alone."""

    model_config = ConfigDict(extra="forbid")

    description: str
    reason: str


class ProviderCodeUnderstandingResult(BaseModel):
    """Internal provider contract excluding deterministic Stage 3 metadata."""

    model_config = ConfigDict(extra="forbid")

    project_summary: str
    architecture: str
    business_rules: list[str] = Field(default_factory=list)
    execution_flows: list[ProviderSemanticFlow] = Field(default_factory=list)
    ambiguities: list[ProviderSemanticAmbiguity] = Field(default_factory=list)


class CodeUnderstandingWithTestsResult(CodeUnderstandingResult):
    """Stage 3 artifact enriched by the integrated Stage 4 pipeline."""

    test_generation: TestGenerationResult


class CodeUnderstandingWithVerificationResult(CodeUnderstandingWithTestsResult):
    """Stage 3 and 4 artifacts enriched by optional Stage 5 verification."""

    test_verification: TestVerificationResult


class CodeUnderstandingWithQualityResult(CodeUnderstandingWithVerificationResult):
    """Integrated Stage 3-6 artifact."""

    quality_evaluation: QualityEvaluation


class CodeUnderstandingWithOptimizationResult(CodeUnderstandingWithQualityResult):
    """Integrated artifact including the complete Stage 6 optimization history."""

    quality_optimization: QualityLoopResult


class CodeUnderstandingWithRuntimePreparationResult(
    CodeUnderstandingWithOptimizationResult
):
    """Stage 3-6 artifacts enriched by the runtime-preparation plan."""

    runtime_execution_plan: RuntimeExecutionPlan


class StructuredOutputClient(Protocol):
    """Provider-neutral boundary implemented by the configured LLM client."""

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        max_completion_tokens: int | None = None,
        context: object | None = None,
        max_file_characters: int = 2500,
        max_total_characters: int = 10000,
    ) -> BaseModel: ...


class CodeUnderstandingAgent:
    """Produce the Stage 3 artifact using deterministic Python analysis."""

    def __init__(self, client: StructuredOutputClient | None = None) -> None:
        # Retained only for construction compatibility. Stage 3A never invokes it.
        self._client = client

    def analyze(
        self,
        context: CodeUnderstandingContext,
        *,
        max_file_characters: int = 2500,
        max_total_characters: int = 10000,
    ) -> CodeUnderstandingResult:
        from app.services.code_understanding.static_analyzer import (
            PythonStaticAnalyzer,
        )

        return PythonStaticAnalyzer().analyze(context)

    def analyze_with_artifacts(
        self,
        context: CodeUnderstandingContext,
        *,
        max_file_characters: int = 2500,
        max_total_characters: int = 10000,
    ) -> tuple[None, CodeUnderstandingResult]:
        """Return a deterministic artifact without a provider response."""
        enriched = self.analyze(context)
        enriched.assert_no_ellipsis()
        enriched_size = self._serialized_size(
            enriched.model_dump(mode="json")
        )
        enriched_tokens = max(1, (enriched_size + 3) // 4)
        logger.info(
            "Stage 3 deterministic output size chars=%d tokens=%d",
            enriched_size,
            enriched_tokens,
        )
        return None, enriched

    @staticmethod
    def _provider_result(response: BaseModel | Any) -> ProviderCodeUnderstandingResult:
        """Normalize legacy injected external models into the lean contract."""
        payload = (
            response.model_dump(mode="json")
            if isinstance(response, BaseModel)
            else response
        )
        if not isinstance(payload, dict):
            return ProviderCodeUnderstandingResult.model_validate(payload)
        allowed = ProviderCodeUnderstandingResult.model_fields
        lean = {key: value for key, value in payload.items() if key in allowed}
        if "business_rules" in lean:
            lean["business_rules"] = [
                item if isinstance(item, str) else item.get("description", "")
                for item in lean["business_rules"]
                if isinstance(item, (str, dict))
            ]
        if "execution_flows" in lean:
            lean["execution_flows"] = [
                {"name": item.get("name", "Flow"), "steps": item.get("steps", [])}
                for item in lean["execution_flows"]
                if isinstance(item, dict)
            ]
        if "ambiguities" in lean:
            lean["ambiguities"] = [
                {
                    "description": item.get("description", ""),
                    "reason": item.get("reason", "Not established by source"),
                }
                for item in lean["ambiguities"]
                if isinstance(item, dict)
            ]
        return ProviderCodeUnderstandingResult.model_validate(lean)

    @staticmethod
    def _serialized_size(value: Any) -> int:
        return len(json.dumps(
            value, ensure_ascii=False, separators=(",", ":")
        ))

    @classmethod
    def _enrich_provider_result(
        cls,
        provider: ProviderCodeUnderstandingResult,
        context: CodeUnderstandingContext,
    ) -> CodeUnderstandingResult:
        endpoints = [
            ApiEndpointDescription(
                method=method,
                route=route,
                handler=handler,
                file=file,
                request_type=fact["request_model"],
                response_type=fact["response_model"],
                request_model=fact["request_model"],
                response_model=fact["response_model"],
                dependencies=fact["dependencies"],
                success_status_codes=fact["success_status_codes"],
                error_status_codes=fact["error_status_codes"],
                exception_status_mappings=fact["exception_status_mappings"],
            )
            for (method, route, handler, file), fact
            in cls._source_endpoints(context).items()
        ]
        parsed = cls._parsed_sources(context)
        analyzed_files = [
            AnalyzedFileDescription(
                path=source.path,
                purpose=(
                    "Application entrypoint"
                    if source.is_entry_point else "Source module"
                ),
                key_symbols=list(dict.fromkeys([
                    *source.classes, *source.functions,
                ])),
            )
            for source in context.files
        ]
        components = [
            ArchitectureComponent(
                name=source.path,
                responsibility=(
                    "Application entrypoint"
                    if source.is_entry_point else "Source module"
                ),
                files=[source.path],
                dependencies=list(dict.fromkeys(source.imports)),
            )
            for source in context.files
        ]
        entrypoints = [
            EntrypointDescription(
                path=source.path,
                symbol=(source.functions[0] if source.functions else None),
                purpose="Application entrypoint",
            )
            for source in context.files if source.is_entry_point
        ]
        endpoint_entries = {
            (item.file, item.handler) for item in endpoints if item.handler
        }
        for file, symbol in sorted(endpoint_entries):
            if not any(
                item.path == file and item.symbol == symbol
                for item in entrypoints
            ):
                entrypoints.append(EntrypointDescription(
                    path=file, symbol=symbol, purpose="API endpoint",
                ))
        data_models = cls._data_models(parsed)
        targets = cls._deterministic_test_targets(parsed)
        base = CodeUnderstandingResult(
            project_summary=provider.project_summary,
            architecture=provider.architecture,
            components=components,
            entrypoints=entrypoints,
            api_endpoints=endpoints,
            data_models=data_models,
            pydantic_schemas=cls._pydantic_schemas(context),
            business_rules=[
                BusinessRuleDescription(
                    description=rule,
                    files=cls._matching_files(rule, context),
                )
                for rule in provider.business_rules
            ],
            execution_flows=[
                ExecutionFlowDescription(
                    name=flow.name,
                    entrypoint=(
                        entrypoints[0].symbol or entrypoints[0].path
                        if entrypoints else ""
                    ),
                    steps=flow.steps,
                    files=list(dict.fromkeys(
                        item.path for item in entrypoints
                    )),
                )
                for flow in provider.execution_flows
            ],
            external_dependencies=list(dict.fromkeys(
                dependency
                for source in context.files
                for dependency in source.imports
            )),
            test_targets=targets,
            ambiguities=[
                AmbiguityDescription(
                    description=item.description,
                    reason=item.reason,
                    files=cls._matching_files(item.description, context),
                )
                for item in provider.ambiguities
            ],
            analyzed_files=analyzed_files,
        )
        return base.model_copy(update={
            "test_targets": cls._enrich_test_targets(base, context)
        })

    @staticmethod
    def _parsed_sources(
        context: CodeUnderstandingContext,
    ) -> list[tuple[SourceFileContext, ast.Module]]:
        parsed = []
        for source in context.files:
            if source.language.casefold() != "python" and not source.path.endswith(".py"):
                continue
            try:
                parsed.append((source, ast.parse(source.content)))
            except SyntaxError:
                continue
        return parsed

    @staticmethod
    def _matching_files(
        description: str, context: CodeUnderstandingContext
    ) -> list[str]:
        tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", description.casefold()))
        matches = [
            source.path for source in context.files
            if tokens.intersection(re.findall(
                r"[A-Za-z_][A-Za-z0-9_]{2,}", source.content.casefold()
            ))
        ]
        return matches or [source.path for source in context.files]

    @classmethod
    def _data_models(
        cls, parsed: list[tuple[SourceFileContext, ast.Module]]
    ) -> list[DataModelDescription]:
        return [
            DataModelDescription(
                name=node.name,
                file=source.path,
                fields=[
                    item.target.id
                    for item in node.body
                    if isinstance(item, ast.AnnAssign)
                    and isinstance(item.target, ast.Name)
                ],
            )
            for source, tree in parsed
            for node in tree.body
            if isinstance(node, ast.ClassDef)
        ]

    @classmethod
    def _deterministic_test_targets(
        cls, parsed: list[tuple[SourceFileContext, ast.Module]]
    ) -> list[TestTargetDescription]:
        targets = []
        for source, tree in parsed:
            for node in cls._runtime_function_nodes(tree):
                if not cls._is_executable_target(node):
                    continue
                collector = _ExecutableNodeCollector()
                for statement in node.body:
                    collector.visit(statement)
                calls = sorted({
                    name
                    for item in collector.nodes
                    if isinstance(item, ast.Call)
                    and (name := cls._call_name(item.func)) is not None
                    and not cls._non_runtime_call(item)
                    and cls._is_collaborator_call(item, node, tree)
                })
                targets.append(TestTargetDescription(
                    symbol=node.name,
                    file=source.path,
                    line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    behavior=ast.get_docstring(node) or f"Execute {node.name}",
                    dependencies=calls,
                    side_effects=sorted({
                        item.func.attr
                        for item in collector.nodes
                        if isinstance(item, ast.Call)
                        and isinstance(item.func, ast.Attribute)
                        and item.func.attr in {
                            "add", "delete", "commit", "rollback", "write",
                            "unlink", "send", "publish",
                        }
                    }),
                    exceptions=sorted({
                        cls._call_name(item.exc.func if isinstance(item.exc, ast.Call) else item.exc)
                        for item in collector.nodes
                        if isinstance(item, ast.Raise) and item.exc is not None
                        and cls._call_name(item.exc.func if isinstance(item.exc, ast.Call) else item.exc)
                    }),
                ))
        return targets

    _CONTAINER_METHODS = frozenset({
        "append", "clear", "copy", "count", "extend", "index", "insert",
        "items", "keys", "pop", "popitem", "reverse", "setdefault", "sort",
        "strip", "values",
    })

    @classmethod
    def _is_collaborator_call(
        cls,
        call: ast.Call,
        function: ast.FunctionDef | ast.AsyncFunctionDef,
        tree: ast.Module,
    ) -> bool:
        """Return whether a call represents a mockable application dependency.

        Dependency targets are collaborators, not an inventory of every Python
        operation performed by the target.  Imported third-party/project symbols
        and calls through parameters are retained; built-ins, container helpers,
        and standard-library utilities are implementation details.
        """
        name = cls._call_name(call.func)
        if not name or py_keyword.iskeyword(name):
            return False

        leaf = name.rsplit(".", 1)[-1]
        if leaf in cls._CONTAINER_METHODS:
            return False
        if isinstance(call.func, ast.Name) and call.func.id in vars(builtins):
            return False

        expression = ast.unparse(call.func)
        root = expression.split(".", 1)[0]
        if leaf in {"add", "discard", "get", "remove", "update"}:
            container_names = {
                argument.arg
                for argument in [
                    *function.args.posonlyargs,
                    *function.args.args,
                    *function.args.kwonlyargs,
                ]
                if argument.annotation is not None
                and ast.unparse(argument.annotation).split("[", 1)[0]
                in {
                    "dict", "Dict", "list", "List", "Mapping",
                    "MutableMapping", "MutableSequence", "Sequence",
                    "set", "Set",
                }
            }
            container_names.update(
                target.id
                for statement in ast.walk(function)
                if isinstance(statement, (ast.Assign, ast.AnnAssign))
                and isinstance(
                    statement.value,
                    (ast.Dict, ast.List, ast.Set, ast.Tuple, ast.DictComp,
                     ast.ListComp, ast.SetComp),
                )
                for target in (
                    statement.targets
                    if isinstance(statement, ast.Assign)
                    else [statement.target]
                )
                if isinstance(target, ast.Name)
            )
            container_names.update(
                target.id
                for statement in ast.walk(function)
                if isinstance(statement, (ast.Assign, ast.AnnAssign))
                and isinstance(statement.value, ast.Call)
                and isinstance(statement.value.func, ast.Name)
                and statement.value.func.id in {"dict", "list", "set", "tuple"}
                for target in (
                    statement.targets
                    if isinstance(statement, ast.Assign)
                    else [statement.target]
                )
                if isinstance(target, ast.Name)
            )
            if root in container_names:
                return False
        imported_modules: dict[str, str] = {}
        for statement in tree.body:
            if isinstance(statement, ast.Import):
                for alias in statement.names:
                    imported_modules[alias.asname or alias.name.split(".", 1)[0]] = alias.name
            elif isinstance(statement, ast.ImportFrom) and statement.module:
                for alias in statement.names:
                    imported_modules[alias.asname or alias.name] = statement.module

        module = imported_modules.get(root)
        if module and module.split(".", 1)[0] in sys.stdlib_module_names:
            return False
        return True

    @staticmethod
    def _runtime_function_nodes(
        tree: ast.Module,
    ) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
        return [
            function
            for node in tree.body
            for function in (
                [node]
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                else [
                    item for item in node.body
                    if isinstance(item, (
                        ast.FunctionDef, ast.AsyncFunctionDef
                    ))
                ]
                if isinstance(node, ast.ClassDef)
                else []
            )
        ]

    @classmethod
    def _is_executable_target(
        cls, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> bool:
        if node.name.startswith("__") and node.name.endswith("__"):
            return False
        decorators = {
            cls._call_name(
                decorator.func if isinstance(decorator, ast.Call)
                else decorator
            )
            for decorator in node.decorator_list
        }
        if decorators.intersection({"overload", "abstractmethod"}):
            return False
        body = [
            statement for statement in node.body
            if not (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            )
        ]
        if not body or all(
            isinstance(statement, ast.Pass)
            or (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and statement.value.value is Ellipsis
            )
            for statement in body
        ):
            return False
        if (
            len(body) == 1
            and isinstance(body[0], ast.Raise)
            and isinstance(body[0].exc, ast.Call)
            and cls._call_name(body[0].exc.func) == "NotImplementedError"
        ):
            return False
        return True

    @classmethod
    def _non_runtime_call(cls, call: ast.Call) -> bool:
        name = cls._call_name(call.func)
        if name == "Depends":
            return True
        if not isinstance(call.func, ast.Attribute):
            return False
        root = call.func.value
        while isinstance(root, ast.Attribute):
            root = root.value
        return (
            name in {"get", "post", "put", "patch", "delete", "options", "head"}
            and isinstance(root, ast.Name)
            and root.id.casefold().endswith("router")
        )

    @classmethod
    def _enrich_test_targets(
        cls,
        result: CodeUnderstandingResult,
        context: CodeUnderstandingContext,
    ) -> list[TestTargetDescription]:
        facts: dict[tuple[str, str, int], tuple[list[str], list[str]]] = {}
        for source in context.files:
            if source.language.casefold() != "python" and not source.path.endswith(".py"):
                continue
            try:
                tree = ast.parse(source.content)
            except SyntaxError:
                continue
            for function in cls._runtime_function_nodes(tree):
                collector = _ExecutableNodeCollector()
                for statement in function.body:
                    collector.visit(statement)
                branches: list[str] = []
                edge_cases: list[str] = []
                for node in collector.nodes:
                    if isinstance(node, ast.If):
                        condition = ast.unparse(node.test)
                        branches.extend([condition, f"not ({condition})"])
                        if (
                            isinstance(node.test, ast.Compare)
                            and len(node.test.ops) == 1
                            and len(node.test.comparators) == 1
                            and isinstance(node.test.left, ast.Name)
                            and isinstance(node.test.comparators[0], ast.Constant)
                            and isinstance(node.test.comparators[0].value, (int, float))
                        ):
                            name = node.test.left.id
                            value = node.test.comparators[0].value
                            branches.extend([
                                f"{name} < {value}", f"{name} == {value}",
                                f"{name} > {value}",
                            ])
                    if (
                        isinstance(node, ast.Subscript)
                        and isinstance(node.ctx, ast.Load)
                        and not cls._typing_subscript(node)
                    ):
                        edge_cases.append(
                            f"missing key access may raise KeyError: {ast.unparse(node)}"
                        )
                facts[(source.path, function.name, function.lineno)] = (
                    list(dict.fromkeys(branches)), list(dict.fromkeys(edge_cases))
                )
        enriched = []
        for target in result.test_targets:
            branches, edges = facts.get(
                (target.file, target.symbol, target.line or -1), ([], [])
            )
            enriched.append(target.model_copy(update={
                "branches": list(dict.fromkeys([*target.branches, *branches])),
                "edge_cases": list(dict.fromkeys([*target.edge_cases, *edges])),
            }))
        return enriched

    @staticmethod
    def _typing_subscript(node: ast.Subscript) -> bool:
        value = node.value
        if isinstance(value, ast.Name):
            return value.id in {
                "Annotated", "Any", "ClassVar", "Dict", "Final", "FrozenSet",
                "Generator", "Iterable", "Iterator", "List", "Literal",
                "Mapping", "Optional", "Sequence", "Set", "Tuple", "Type",
                "Union",
            }
        return (
            isinstance(value, ast.Attribute)
            and isinstance(value.value, ast.Name)
            and value.value.id in {"typing", "typing_extensions"}
        )

    @staticmethod
    def _source_endpoints(
        context: CodeUnderstandingContext,
    ) -> dict[tuple[str, str, str, str], dict[str, Any]]:
        result: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        methods = {"get", "post", "put", "patch", "delete", "options", "head"}
        parsed: list[tuple[SourceFileContext, ast.Module]] = []
        for source in context.files:
            if source.language.casefold() != "python" and not source.path.endswith(".py"):
                continue
            try:
                tree = ast.parse(source.content)
            except SyntaxError:
                continue
            parsed.append((source, tree))

        module_files = {
            CodeUnderstandingAgent._module_name(source.path): source.path
            for source, _ in parsed
        }
        router_prefixes: dict[tuple[str, str], str] = {}
        imports: dict[str, dict[str, tuple[str, str | None]]] = {}
        for source, tree in parsed:
            bindings: dict[str, tuple[str, str | None]] = {}
            for statement in tree.body:
                if isinstance(statement, ast.Import):
                    for alias in statement.names:
                        bindings[alias.asname or alias.name.split(".")[0]] = (
                            alias.name, None
                        )
                elif isinstance(statement, ast.ImportFrom):
                    imported_module = statement.module or ""
                    if statement.level:
                        package = CodeUnderstandingAgent._module_name(
                            source.path
                        ).split(".")
                        if not source.path.replace("\\", "/").endswith(
                            "/__init__.py"
                        ):
                            package = package[:-1]
                        package = package[
                            :max(0, len(package) - statement.level + 1)
                        ]
                        imported_module = ".".join([
                            *package,
                            *([imported_module] if imported_module else []),
                        ])
                    for alias in statement.names:
                        bindings[alias.asname or alias.name] = (
                            ".".join(filter(None, [
                                imported_module, alias.name
                            ])),
                            alias.name,
                        )
                elif isinstance(statement, (ast.Assign, ast.AnnAssign)):
                    targets = (
                        statement.targets
                        if isinstance(statement, ast.Assign)
                        else [statement.target]
                    )
                    value = statement.value
                    if (
                        isinstance(value, ast.Call)
                        and CodeUnderstandingAgent._call_name(value.func)
                        == "APIRouter"
                    ):
                        prefix = CodeUnderstandingAgent._string_keyword(
                            value, "prefix"
                        ) or ""
                        for target in targets:
                            if isinstance(target, ast.Name):
                                router_prefixes[(source.path, target.id)] = prefix
            imports[source.path] = bindings

        def resolve_router(file: str, expression: ast.AST) -> tuple[str, str] | None:
            if isinstance(expression, ast.Name):
                local = (file, expression.id)
                if local in router_prefixes:
                    return local
                binding = imports.get(file, {}).get(expression.id)
                if binding and binding[1]:
                    module = binding[0].rsplit(".", 1)[0]
                    candidate = (module_files.get(module, ""), binding[1])
                    return candidate if candidate in router_prefixes else None
            if isinstance(expression, ast.Attribute) and isinstance(
                expression.value, ast.Name
            ):
                binding = imports.get(file, {}).get(expression.value.id)
                if binding:
                    candidate = (
                        module_files.get(binding[0], ""), expression.attr
                    )
                    return candidate if candidate in router_prefixes else None
            return None

        inclusions: dict[
            tuple[str, str], list[tuple[tuple[str, str] | None, str]]
        ] = {}
        for source, tree in parsed:
            for call in (
                item for item in ast.walk(tree) if isinstance(item, ast.Call)
            ):
                if (
                    not isinstance(call.func, ast.Attribute)
                    or call.func.attr != "include_router"
                    or not call.args
                ):
                    continue
                child = resolve_router(source.path, call.args[0])
                if child is None:
                    continue
                parent = resolve_router(source.path, call.func.value)
                inclusions.setdefault(child, []).append((
                    parent,
                    CodeUnderstandingAgent._string_keyword(
                        call, "prefix"
                    ) or "",
                ))

        def mount_prefixes(
            router: tuple[str, str],
            visited: frozenset[tuple[str, str]] = frozenset(),
        ) -> list[str]:
            if router in visited:
                return [""]
            mounted = inclusions.get(router)
            if not mounted:
                return [""]
            prefixes = []
            for parent, include_prefix in mounted:
                if parent is None:
                    prefixes.append(include_prefix)
                else:
                    for ancestor in mount_prefixes(parent, visited | {router}):
                        prefixes.append(CodeUnderstandingAgent._join_route(
                            ancestor, router_prefixes.get(parent, ""),
                            include_prefix,
                        ))
            return list(dict.fromkeys(prefixes))

        exception_statuses: dict[str, int] = {}
        function_entries: dict[
            str, list[tuple[set[str], list[ExceptionStatusMapping]]]
        ] = {}
        pydantic_names = {
            node.name
            for _, tree in parsed
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and any(
                CodeUnderstandingAgent._call_name(base) == "BaseModel"
                for base in node.bases
            )
        }
        for _, tree in parsed:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    status = CodeUnderstandingAgent._exception_status(node)
                    if status is not None:
                        exception_statuses[node.name] = status
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    calls = {
                        CodeUnderstandingAgent._call_name(item.func)
                        for item in ast.walk(node)
                        if isinstance(item, ast.Call)
                    } - {None}
                    mappings = CodeUnderstandingAgent._raised_statuses(
                        node, exception_statuses
                    )
                    function_entries.setdefault(node.name, []).append(
                        (calls, mappings)
                    )
        functions = {
            name: entries[0]
            for name, entries in function_entries.items()
            if len(entries) == 1
        }

        for source, tree in parsed:
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for decorator in node.decorator_list:
                    if not isinstance(decorator, ast.Call) or not decorator.args:
                        continue
                    function = decorator.func
                    method = function.attr.casefold() if isinstance(function, ast.Attribute) else ""
                    route = decorator.args[0]
                    if method in methods and isinstance(route, ast.Constant) and isinstance(route.value, str):
                        success, errors = CodeUnderstandingAgent._decorator_statuses(
                            decorator
                        )
                        if not success:
                            success.add(200)
                        mappings = {
                            (item.exception, item.status_code): item
                            for item in CodeUnderstandingAgent._transitive_mappings(
                                node.name, functions
                            )
                        }
                        mappings.update({
                            (item.exception, item.status_code): item
                            for item in CodeUnderstandingAgent._raised_statuses(
                                node, exception_statuses
                            )
                        })
                        ordered_mappings = [
                            mappings[key] for key in sorted(mappings)
                        ]
                        errors.update(
                            item.status_code for item in ordered_mappings
                        )
                        request_model = CodeUnderstandingAgent._request_model(
                            node, pydantic_names
                        )
                        response_model = CodeUnderstandingAgent._keyword_type(
                            decorator, "response_model"
                        )
                        dependencies = CodeUnderstandingAgent._dependencies(
                            node, decorator
                        )
                        owner = (
                            function.value
                            if isinstance(function, ast.Attribute)
                            else None
                        )
                        router = (
                            resolve_router(source.path, owner)
                            if owner is not None else None
                        )
                        prefixes = (
                            mount_prefixes(router) if router is not None else [""]
                        )
                        router_prefix = (
                            router_prefixes.get(router, "")
                            if router is not None else ""
                        )
                        for mounted_prefix in prefixes:
                            final_route = CodeUnderstandingAgent._join_route(
                                mounted_prefix, router_prefix, route.value
                            )
                            result[(
                                method.upper(), final_route, node.name, source.path
                            )] = {
                                "request_model": request_model,
                                "response_model": response_model,
                                "dependencies": dependencies,
                                "success_status_codes": sorted(success),
                                "error_status_codes": sorted(errors),
                                "exception_status_mappings": ordered_mappings,
                            }
        return result

    @staticmethod
    def _module_name(path: str) -> str:
        module = path.replace("\\", "/").removesuffix(".py").replace("/", ".")
        return module.removesuffix(".__init__")

    @staticmethod
    def _string_keyword(call: ast.Call, name: str) -> str | None:
        return next(
            (
                keyword.value.value
                for keyword in call.keywords
                if keyword.arg == name
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, str)
            ),
            None,
        )

    @staticmethod
    def _join_route(*parts: str) -> str:
        nonempty = [part for part in parts if part]
        if not nonempty:
            return "/"
        trailing_slash = nonempty[-1].endswith("/")
        route = "/" + "/".join(
            part.strip("/") for part in nonempty if part.strip("/")
        )
        if route != "/" and trailing_slash:
            route += "/"
        return route

    @classmethod
    def _dependencies(
        cls,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        decorator: ast.Call,
    ) -> list[str]:
        dependencies: list[str] = []

        def collect(value: ast.AST | None) -> None:
            if value is None:
                return
            for item in ast.walk(value):
                if (
                    isinstance(item, ast.Call)
                    and cls._call_name(item.func) == "Depends"
                ):
                    dependencies.append(
                        ast.unparse(item.args[0]) if item.args else "Depends"
                    )

        for default in [*node.args.defaults, *node.args.kw_defaults]:
            collect(default)
        for argument in [
            *node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs
        ]:
            collect(argument.annotation)
        for keyword in decorator.keywords:
            if keyword.arg == "dependencies":
                collect(keyword.value)
        return list(dict.fromkeys(dependencies))

    @staticmethod
    def _status_value(node: ast.AST | None) -> int | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return node.value if 100 <= node.value <= 599 else None
        name = ast.unparse(node) if node is not None else ""
        match = re.search(r"(?:^|\.)HTTP_(\d{3})(?:_|$)", name)
        return int(match.group(1)) if match else None

    @classmethod
    def _decorator_statuses(
        cls, decorator: ast.Call
    ) -> tuple[set[int], set[int]]:
        success: set[int] = set()
        errors: set[int] = set()
        for keyword in decorator.keywords:
            if keyword.arg == "status_code":
                status = cls._status_value(keyword.value)
                if status is not None:
                    (errors if status >= 400 else success).add(status)
            elif keyword.arg == "responses" and isinstance(keyword.value, ast.Dict):
                for key in keyword.value.keys:
                    status = cls._status_value(key)
                    if status is not None:
                        (errors if status >= 400 else success).add(status)
        return success, errors

    @classmethod
    def _exception_status(cls, node: ast.ClassDef) -> int | None:
        for item in ast.walk(node):
            if not isinstance(item, ast.Call):
                continue
            for keyword in item.keywords:
                if keyword.arg == "status_code":
                    status = cls._status_value(keyword.value)
                    if status is not None:
                        return status
        return None

    @classmethod
    def _raised_statuses(
        cls, node: ast.FunctionDef | ast.AsyncFunctionDef,
        exception_statuses: dict[str, int],
    ) -> list[ExceptionStatusMapping]:
        mappings: dict[tuple[str, int], ExceptionStatusMapping] = {}
        for item in ast.walk(node):
            if not isinstance(item, ast.Raise) or item.exc is None:
                continue
            call = item.exc if isinstance(item.exc, ast.Call) else None
            name = cls._call_name(call.func) if call else cls._call_name(item.exc)
            if name in exception_statuses:
                status = exception_statuses[name]
                mappings[(name, status)] = ExceptionStatusMapping(
                    exception=name, status_code=status
                )
            if call and name == "HTTPException":
                status = next(
                    (
                        cls._status_value(keyword.value)
                        for keyword in call.keywords
                        if keyword.arg == "status_code"
                    ),
                    None,
                )
                if status is not None:
                    mappings[(name, status)] = ExceptionStatusMapping(
                        exception=name, status_code=status
                    )
        return list(mappings.values())

    @staticmethod
    def _call_name(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None

    @classmethod
    def _transitive_mappings(
        cls,
        function_name: str,
        functions: dict[str, tuple[set[str], list[ExceptionStatusMapping]]],
    ) -> list[ExceptionStatusMapping]:
        pending, visited = [function_name], set()
        mappings: dict[tuple[str, int], ExceptionStatusMapping] = {}
        while pending:
            current = pending.pop()
            if current in visited or current not in functions:
                continue
            visited.add(current)
            calls, direct = functions[current]
            mappings.update(
                ((item.exception, item.status_code), item)
                for item in direct
            )
            pending.extend(sorted(calls - visited))
        return [
            mappings[key] for key in sorted(mappings)
        ]

    @staticmethod
    def _keyword_type(call: ast.Call, name: str) -> str | None:
        for keyword in call.keywords:
            if keyword.arg == name:
                return ast.unparse(keyword.value)
        return None

    @staticmethod
    def _request_model(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        pydantic_names: set[str],
    ) -> str | None:
        arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        for argument in arguments:
            if argument.annotation is None:
                continue
            annotation = ast.unparse(argument.annotation)
            matches = [
                name for name in sorted(pydantic_names)
                if re.search(rf"\b{re.escape(name)}\b", annotation)
            ]
            if len(matches) == 1:
                return matches[0]
        return None

    @classmethod
    def _pydantic_schemas(
        cls, context: CodeUnderstandingContext
    ) -> list[PydanticSchemaDescription]:
        schemas = []
        for source in context.files:
            if source.language.casefold() != "python" and not source.path.endswith(".py"):
                continue
            try:
                tree = ast.parse(source.content)
            except SyntaxError:
                continue
            for node in tree.body:
                if not isinstance(node, ast.ClassDef) or not any(
                    cls._call_name(base) == "BaseModel" for base in node.bases
                ):
                    continue
                fields = []
                for item in node.body:
                    if not isinstance(item, ast.AnnAssign) or not isinstance(
                        item.target, ast.Name
                    ):
                        continue
                    has_default, default, examples = cls._field_metadata(item.value)
                    annotation = ast.unparse(item.annotation)
                    optional = (
                        "Optional[" in annotation
                        or re.search(r"(?:^|\s)\|\s*None(?:\s|$)", annotation)
                        is not None
                        or (has_default and default is None)
                    )
                    fields.append(PydanticFieldDescription(
                        name=item.target.id,
                        type=annotation,
                        required=not has_default,
                        optional=optional,
                        has_default=has_default,
                        default=default,
                        examples=examples,
                        **cls._field_constraints(
                            item.annotation, item.value
                        ),
                    ))
                schemas.append(PydanticSchemaDescription(
                    name=node.name,
                    file=source.path,
                    fields=fields,
                    validators=cls._pydantic_validators(node),
                    examples=cls._schema_examples(node),
                ))
        return schemas

    @classmethod
    def _field_constraints(
        cls, annotation: ast.AST, value: ast.AST | None
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "min_length": None,
            "max_length": None,
            "pattern": None,
            "regex": None,
            "gt": None,
            "lt": None,
            "ge": None,
            "le": None,
            "description": None,
            "title": None,
            "default_factory": None,
        }
        field_calls = [
            item
            for root in (annotation, value)
            if root is not None
            for item in ast.walk(root)
            if isinstance(item, ast.Call)
            and cls._call_name(item.func) == "Field"
        ]
        for call in field_calls:
            for keyword in call.keywords:
                if keyword.arg in metadata:
                    metadata[keyword.arg] = (
                        ast.unparse(keyword.value)
                        if keyword.arg == "default_factory"
                        else cls._literal(keyword.value)
                    )
        return metadata

    @classmethod
    def _pydantic_validators(
        cls, node: ast.ClassDef
    ) -> list[PydanticValidatorDescription]:
        validators = []
        decorator_names = {
            "validator", "root_validator", "field_validator", "model_validator"
        }
        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in item.decorator_list:
                call = decorator if isinstance(decorator, ast.Call) else None
                function = call.func if call is not None else decorator
                name = cls._call_name(function)
                if name not in decorator_names:
                    continue
                fields = []
                if call is not None and name in {"validator", "field_validator"}:
                    fields = [
                        literal
                        for argument in call.args
                        if isinstance((literal := cls._literal(argument)), str)
                    ]
                mode = None
                if call is not None:
                    mode = next(
                        (
                            cls._literal(keyword.value)
                            for keyword in call.keywords
                            if keyword.arg == "mode"
                        ),
                        None,
                    )
                    if mode is None and any(
                        keyword.arg == "pre"
                        and cls._literal(keyword.value) is True
                        for keyword in call.keywords
                    ):
                        mode = "before"
                validators.append(PydanticValidatorDescription(
                    name=item.name,
                    fields=fields,
                    mode=mode if isinstance(mode, str) else None,
                    decorator=ast.unparse(decorator),
                    is_async=isinstance(item, ast.AsyncFunctionDef),
                ))
        return validators

    @classmethod
    def _field_metadata(
        cls, value: ast.AST | None
    ) -> tuple[bool, Any | None, list[Any]]:
        if value is None:
            return False, None, []
        if isinstance(value, ast.Call) and cls._call_name(value.func) == "Field":
            default_node = value.args[0] if value.args else None
            has_default_factory = False
            examples: list[Any] = []
            for keyword in value.keywords:
                if keyword.arg == "default":
                    default_node = keyword.value
                elif keyword.arg == "default_factory":
                    has_default_factory = True
                elif keyword.arg in {"example", "examples"}:
                    literal = cls._literal(keyword.value)
                    if literal is not None:
                        examples.extend(
                            literal if isinstance(literal, list) else [literal]
                        )
            default = cls._literal(default_node)
            has_default = has_default_factory or (
                default_node is not None and not (
                    isinstance(default_node, ast.Constant)
                    and default_node.value is Ellipsis
                )
            )
            return has_default, default, examples
        return True, cls._literal(value), []

    @staticmethod
    def _literal(node: ast.AST | None) -> Any | None:
        if node is None:
            return None
        try:
            return CodeUnderstandingAgent._replace_ellipsis(
                ast.literal_eval(node)
            )
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _replace_ellipsis(value: Any) -> Any:
        """Normalize Python required-field sentinels into JSON-safe values."""
        if value is Ellipsis:
            return None
        if isinstance(value, dict):
            return {
                key: CodeUnderstandingAgent._replace_ellipsis(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [
                CodeUnderstandingAgent._replace_ellipsis(item)
                for item in value
            ]
        if isinstance(value, tuple):
            return tuple(
                CodeUnderstandingAgent._replace_ellipsis(item)
                for item in value
            )
        if isinstance(value, set):
            return {
                CodeUnderstandingAgent._replace_ellipsis(item)
                for item in value
            }
        return value

    @classmethod
    def _schema_examples(cls, node: ast.ClassDef) -> list[Any]:
        examples: list[Any] = []
        for item in node.body:
            if isinstance(item, ast.ClassDef) and item.name == "Config":
                examples.extend(cls._schema_examples(item))
                continue
            if not isinstance(item, ast.Assign):
                continue
            names = {
                target.id for target in item.targets if isinstance(target, ast.Name)
            }
            if not names.intersection({"model_config", "schema_extra"}):
                continue
            literal = cls._literal(item.value)
            if (
                literal is None
                and isinstance(item.value, ast.Call)
                and cls._call_name(item.value.func) == "ConfigDict"
            ):
                literal = {
                    keyword.arg: cls._literal(keyword.value)
                    for keyword in item.value.keywords
                    if keyword.arg is not None
                }
            if not isinstance(literal, dict):
                continue
            extra = literal.get("json_schema_extra", literal)
            if isinstance(extra, dict):
                value = extra.get("examples", extra.get("example"))
                if value is not None:
                    examples.extend(value if isinstance(value, list) else [value])
        return examples
