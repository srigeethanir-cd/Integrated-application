"""Deterministic Python static analysis for Stage 3A."""

from __future__ import annotations

import ast
import keyword
from pathlib import PurePosixPath

from app.agents.code_understanding.agent import (
    AnalyzedFileDescription,
    ApiEndpointDescription,
    ArchitectureComponent,
    BusinessRuleDescription,
    CallGraphEdge,
    ClassDescription,
    CodeUnderstandingAgent,
    CodeUnderstandingContext,
    CodeUnderstandingResult,
    DataModelDescription,
    EntrypointDescription,
    ExecutionFlowDescription,
    FunctionDescription,
    ImportDescription,
    ModuleDescription,
    RepositoryBehaviorContext,
    SecurityFindingDescription,
    SQLAlchemyColumnDescription,
    SQLAlchemySessionFactoryDescription,
    SymbolDescription,
)

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


class _RuntimeAstVisitor(ast.NodeVisitor):
    """Visit executable expressions while excluding metadata-only AST."""

    def __init__(self) -> None:
        self.calls: list[ast.Call] = []
        self.subscripts: list[ast.Subscript] = []

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

    def visit_Call(self, node: ast.Call) -> None:
        self.calls.append(node)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        self.subscripts.append(node)
        self.generic_visit(node)


class PythonStaticAnalyzer:
    """Build the backward-compatible Stage 3 result from Python source."""

    _HTTP_METHODS = {
        "get", "post", "put", "patch", "delete", "options", "head", "trace"
    }
    _SQLALCHEMY_CALLS = {
        "add", "add_all", "commit", "delete", "execute", "filter",
        "filter_by", "flush", "get", "query", "refresh", "rollback",
        "scalar", "scalars", "select", "update",
    }

    def analyze(self, context: CodeUnderstandingContext) -> CodeUnderstandingResult:
        parsed = CodeUnderstandingAgent._parsed_sources(context)
        module_names = self._module_names(parsed)
        findings = [
            SecurityFindingDescription.model_validate(item)
            for item in context.security_findings
        ]
        modules: list[ModuleDescription] = []
        imports: list[ImportDescription] = []
        functions: list[FunctionDescription] = []
        classes: list[ClassDescription] = []
        symbols: list[SymbolDescription] = []
        call_graph: list[CallGraphEdge] = []

        for source, tree in parsed:
            module = module_names[source.path]
            file_imports = self._imports(source.path, tree)
            imports.extend(file_imports)
            modules.append(ModuleDescription(
                name=module,
                file=source.path,
                imports=self._module_dependencies(tree, module, source.path),
                runtime_resolvable=self._runtime_resolvable(module),
            ))
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    qualified = f"{module}.{node.name}"
                    related = self._related_findings(findings, source.path, node)
                    methods = [
                        item for item in node.body
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ]
                    usage = self._sqlalchemy_usage(node)
                    inheritance = [
                        ast.unparse(item) for item in node.bases
                    ]
                    classes.append(ClassDescription(
                        name=node.name,
                        qualified_name=qualified,
                        module=module,
                        file=source.path,
                        line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        fields=self._class_fields(
                            parsed, source.path, node.name
                        ),
                        bases=inheritance,
                        inheritance=inheritance,
                        decorators=[ast.unparse(item) for item in node.decorator_list],
                        methods=[item.name for item in methods],
                        sqlalchemy_model_usage=usage,
                        constructor_dependencies=self._constructor_dependencies(methods),
                        target_classification=self._class_classification(
                            source.path, node
                        ),
                        target_priority=self._class_priority(source.path, node),
                        runtime_resolvable=self._runtime_resolvable(qualified),
                        security_findings=related,
                    ))
                    symbols.append(self._symbol(
                        node.name, qualified, "class", source.path, node
                    ))
                    for method in methods:
                        function = self._function(
                            method, source.path, f"{qualified}.{method.name}",
                            qualified, findings,
                        )
                        functions.append(function)
                        symbols.append(self._symbol(
                            method.name, function.qualified_name, "method",
                            source.path, method, qualified,
                        ))
                        call_graph.extend(self._calls(
                            method, function.qualified_name, source.path
                        ))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qualified = f"{module}.{node.name}"
                    function = self._function(
                        node, source.path, qualified, None, findings
                    )
                    functions.append(function)
                    symbols.append(self._symbol(
                        node.name, qualified, "function", source.path, node
                    ))
                    call_graph.extend(self._calls(node, qualified, source.path))

        call_graph = self._build_call_graph(parsed, module_names)
        calls_by_caller: dict[str, list[str]] = {}
        for edge in call_graph:
            calls_by_caller.setdefault(edge.caller, []).append(edge.callee)
        functions = [
            item.model_copy(update={
                "calls": sorted(set(calls_by_caller.get(
                    item.qualified_name, []
                )))
            })
            for item in functions
        ]
        endpoints = self._endpoints(parsed, functions, classes, findings)
        functions = self._classify_functions(functions, endpoints, call_graph)
        data_models = []
        for item in classes:
            model_node = self._class_node(parsed, item.file, item.name)
            sqlalchemy = self._sqlalchemy_model_metadata(model_node)
            data_models.append(DataModelDescription(
                name=item.name,
                file=item.file,
                fields=self._class_fields(parsed, item.file, item.name),
                columns=sqlalchemy["columns"],
                primary_keys=sqlalchemy["primary_keys"],
                foreign_keys=sqlalchemy["foreign_keys"],
                relationships=sqlalchemy["relationships"],
                constraints=sqlalchemy["constraints"],
                indexes=sqlalchemy["indexes"],
                unique_constraints=sqlalchemy["unique_constraints"],
                check_constraints=sqlalchemy["check_constraints"],
                methods=item.methods,
                decorators=item.decorators,
                sqlalchemy_model_usage=item.sqlalchemy_model_usage,
                security_findings=item.security_findings,
            ))
        targets = CodeUnderstandingAgent._deterministic_test_targets(parsed)
        targets = CodeUnderstandingAgent._enrich_test_targets(
            CodeUnderstandingResult(
                project_summary="", architecture="", test_targets=targets
            ),
            context,
        )
        function_lookup = {
            (item.file, item.name, item.line): item for item in functions
        }
        targets = [
            item.model_copy(update={
                "qualified_name": function_lookup[(item.file, item.symbol, item.line)].qualified_name,
                "module": function_lookup[(item.file, item.symbol, item.line)].module,
                "owner_class": function_lookup[(item.file, item.symbol, item.line)].owner_class,
                "target_classification": function_lookup[(item.file, item.symbol, item.line)].target_classification,
                "target_priority": function_lookup[(item.file, item.symbol, item.line)].target_priority,
                "is_primary": function_lookup[(item.file, item.symbol, item.line)].target_classification != "router_wrapper",
                "runtime_resolvable": function_lookup[(item.file, item.symbol, item.line)].runtime_resolvable,
                "delegated_targets": self._delegated_targets(
                    function_lookup[(item.file, item.symbol, item.line)], call_graph, functions
                ),
                "security_findings": (
                    function_lookup[(item.file, item.symbol, item.line)].security_findings
                )
            })
            for item in targets
            if (item.file, item.symbol, item.line) in function_lookup
        ]
        targets = self._authoritative_targets(targets)
        entrypoints = self._entrypoints(context, endpoints)
        components = [
            ArchitectureComponent(
                name=item.name,
                responsibility=(
                    "Application entrypoint"
                    if next(
                        source.is_entry_point for source in context.files
                        if source.path == item.file
                    )
                    else "Python module"
                ),
                files=[item.file],
                dependencies=item.imports,
            )
            for item in modules
        ]
        external_dependencies = sorted({
            item.module.split(".")[0]
            for item in imports if item.level == 0
        })
        business_rules = self._business_rules(parsed)
        flows = [
            ExecutionFlowDescription(
                name=f"{item.method} {item.route}",
                entrypoint=item.handler or "",
                steps=[
                    f"Invoke {item.handler}",
                    *[
                        f"Call {edge.callee}"
                        for edge in call_graph
                        if edge.caller.endswith(f".{item.handler}")
                    ],
                ],
                files=[item.file],
            )
            for item in endpoints
        ]
        python_files = len(parsed)
        result = CodeUnderstandingResult(
            project_summary=(
                f"Python project with {python_files} module"
                f"{'' if python_files == 1 else 's'}, {len(functions)} callable"
                f"{'' if len(functions) == 1 else 's'}, {len(classes)} class"
                f"{'' if len(classes) == 1 else 'es'}, and {len(endpoints)} API endpoint"
                f"{'' if len(endpoints) == 1 else 's'}."
            ),
            architecture=(
                "FastAPI application with deterministic Python static analysis."
                if endpoints else
                "Python application with deterministic static analysis."
            ),
            modules=sorted(modules, key=lambda item: item.file),
            imports=sorted(imports, key=lambda item: (item.file, item.module)),
            functions=sorted(functions, key=lambda item: item.qualified_name),
            classes=sorted(classes, key=lambda item: item.qualified_name),
            symbol_table=sorted(symbols, key=lambda item: item.qualified_name),
            call_graph=sorted(
                call_graph,
                key=lambda item: (item.caller, item.line, item.callee),
            ),
            sqlalchemy_session_factories=self._session_factories(parsed),
            security_findings=findings,
            components=components,
            entrypoints=entrypoints,
            api_endpoints=endpoints,
            data_models=data_models,
            pydantic_schemas=CodeUnderstandingAgent._pydantic_schemas(context),
            business_rules=business_rules,
            execution_flows=flows,
            external_dependencies=external_dependencies,
            test_targets=targets,
            analyzed_files=[
                AnalyzedFileDescription(
                    path=item.file,
                    purpose="Python module",
                    key_symbols=[
                        symbol.name for symbol in symbols
                        if symbol.file == item.file
                    ],
                )
                for item in modules
            ],
            repository_behavior=RepositoryBehaviorContext(
                modules=sorted(modules, key=lambda item: item.file),
                functions=sorted(functions, key=lambda item: item.qualified_name),
                classes=sorted(classes, key=lambda item: item.qualified_name),
                call_graph=sorted(
                    call_graph,
                    key=lambda item: (item.caller, item.line, item.callee),
                ),
                dependency_graph=[
                    {"source": module.name, "target": dependency}
                    for module in sorted(modules, key=lambda item: item.name)
                    for dependency in sorted(module.imports)
                ],
                side_effects={
                    item.qualified_name: item.side_effects
                    for item in functions if item.side_effects
                },
                exceptions={
                    item.qualified_name: item.exceptions
                    for item in functions if item.exceptions
                },
                business_rules=business_rules,
            ),
        )
        result.assert_no_ellipsis()
        return result

    @staticmethod
    def _module_name(path: str) -> str:
        value = PurePosixPath(path)
        parts = list(value.with_suffix("").parts)
        if parts and parts[-1] == "__init__":
            parts.pop()
        return ".".join(parts)

    @classmethod
    def _module_names(cls, parsed) -> dict[str, str]:
        """Infer the import root and map each source path to its real module."""
        paths = {
            source.path: list(PurePosixPath(source.path).with_suffix("").parts)
            for source, _ in parsed
        }
        candidates: set[tuple[str, ...]] = {()}
        for source, _ in parsed:
            parts = list(PurePosixPath(source.path).parts)
            candidates.update(tuple(parts[:index]) for index in range(len(parts)))

        absolute_imports = []
        for _, tree in parsed:
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    absolute_imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    absolute_imports.append(node.module)

        def modules_for(root: tuple[str, ...]) -> set[str]:
            result = set()
            for parts in paths.values():
                if tuple(parts[:len(root)]) != root:
                    continue
                relative = parts[len(root):]
                if relative and relative[-1] == "__init__":
                    relative = relative[:-1]
                if relative:
                    result.add(".".join(relative))
            return result

        def score(root: tuple[str, ...]) -> tuple[int, int, int]:
            modules = modules_for(root)
            resolved = sum(
                any(module == imported or module.startswith(f"{imported}.")
                    for module in modules)
                for imported in absolute_imports
            )
            entrypoint_bonus = sum(
                1 for source, _ in parsed
                if source.is_entry_point
                and tuple(PurePosixPath(source.path).parts[:-1]) == root
            )
            return resolved, entrypoint_bonus, -len(root)

        root = max(candidates, key=score, default=())
        result = {}
        for path, parts in paths.items():
            relative = parts[len(root):] if tuple(parts[:len(root)]) == root else parts
            if relative and relative[-1] == "__init__":
                relative = relative[:-1]
            result[path] = ".".join(relative)
        return result

    @staticmethod
    def _runtime_resolvable(qualified_name: str) -> bool:
        return bool(qualified_name) and all(
            part.isidentifier() and not keyword.iskeyword(part)
            for part in qualified_name.split(".")
        )

    @classmethod
    def _module_dependencies(
        cls, tree: ast.Module, module: str, file: str
    ) -> list[str]:
        package = module if file.replace("\\", "/").endswith(
            "/__init__.py"
        ) else module.rsplit(".", 1)[0] if "." in module else ""
        dependencies = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                dependencies.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported = node.module or ""
                if node.level:
                    parts = package.split(".") if package else []
                    parts = parts[:max(0, len(parts) - node.level + 1)]
                    imported = ".".join(filter(None, [*parts, imported]))
                if imported:
                    dependencies.add(imported)
        return sorted(dependencies)

    @staticmethod
    def _class_classification(file: str, node: ast.ClassDef) -> str:
        path = file.casefold().replace("\\", "/")
        name = node.name.casefold()
        if "/repositories/" in f"/{path}" or name.endswith("repository"):
            return "repository"
        if "/services/" in f"/{path}" or name.endswith("service"):
            return "business_service"
        return "class"

    @classmethod
    def _class_priority(cls, file: str, node: ast.ClassDef) -> str:
        return (
            "high"
            if cls._class_classification(file, node)
            in {"business_service", "repository"}
            else "normal"
        )

    @classmethod
    def _classify_functions(
        cls,
        functions: list[FunctionDescription],
        endpoints: list[ApiEndpointDescription],
        call_graph: list[CallGraphEdge],
    ) -> list[FunctionDescription]:
        endpoint_symbols = {
            (item.file, item.handler) for item in endpoints if item.handler
        }
        known = {item.qualified_name: item for item in functions}
        callees = {
            item.qualified_name: [
                edge.callee for edge in call_graph
                if edge.caller == item.qualified_name and edge.callee in known
            ]
            for item in functions
        }

        def base_classification(item: FunctionDescription) -> str:
            path = f"/{item.file.casefold().replace(chr(92), '/')}/"
            owner = (item.owner_class or "").casefold()
            if "/tests/" in path or PurePosixPath(item.file).name.startswith(
                "test_"
            ):
                return "test_code"
            if "/repositories/" in path or owner.endswith("repository"):
                return "repository"
            if "/services/" in path or owner.endswith("service"):
                return "business_service"
            if "/dependencies/" in path or item.name.startswith("get_"):
                return "dependency_provider"
            if any(part in path for part in ("/utils/", "/utilities/", "/helpers/")):
                return "utility"
            return "method" if item.owner_class else "function"

        initial = {
            item.qualified_name: base_classification(item) for item in functions
        }
        result = []
        for item in functions:
            classification = initial[item.qualified_name]
            if (item.file, item.name) in endpoint_symbols:
                delegates = callees[item.qualified_name]
                classification = (
                    "router_wrapper"
                    if any(
                        initial[target] in {
                            "business_service", "repository", "utility"
                        }
                        for target in delegates
                    )
                    else "endpoint_handler"
                )
            priority = (
                "high"
                if classification in {"business_service", "repository"}
                else "low"
                if classification in {"router_wrapper", "dependency_provider"}
                else "normal"
            )
            result.append(item.model_copy(update={
                "target_classification": classification,
                "target_priority": priority,
                "runtime_resolvable": cls._runtime_resolvable(
                    item.qualified_name
                ),
            }))
        return result

    @staticmethod
    def _delegated_targets(
        function: FunctionDescription,
        call_graph: list[CallGraphEdge],
        functions: list[FunctionDescription],
    ) -> list[str]:
        known = {item.qualified_name for item in functions}
        return sorted({
            edge.callee for edge in call_graph
            if edge.caller == function.qualified_name and edge.callee in known
        })

    @staticmethod
    def _authoritative_targets(
        targets: list,
    ) -> list:
        """Keep unique, importable runtime targets and suppress delegating routes."""
        unique = {}
        for target in targets:
            if not target.runtime_resolvable or target.target_classification == "test_code":
                continue
            if target.target_classification == "router_wrapper" and target.delegated_targets:
                continue
            unique.setdefault(target.qualified_name, target)
        priority = {"high": 0, "normal": 1, "low": 2}
        return sorted(
            unique.values(),
            key=lambda item: (
                priority.get(item.target_priority, 3), item.qualified_name
            ),
        )

    @staticmethod
    def _imports(file: str, tree: ast.Module) -> list[ImportDescription]:
        result = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result.append(ImportDescription(
                        module=alias.name, file=file,
                        names=[alias.asname or alias.name],
                    ))
            elif isinstance(node, ast.ImportFrom):
                result.append(ImportDescription(
                    module=node.module or "",
                    file=file,
                    names=[
                        alias.asname or alias.name for alias in node.names
                    ],
                    level=node.level,
                ))
        return result

    @classmethod
    def _function(
        cls,
        node: FunctionNode,
        file: str,
        qualified: str,
        parent: str | None,
        findings: list[SecurityFindingDescription],
    ) -> FunctionDescription:
        args = [
            *node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs
        ]
        calls = sorted({
            ast.unparse(item.func)
            for statement in node.body
            for item in ast.walk(statement)
            if isinstance(item, ast.Call)
            and CodeUnderstandingAgent._call_name(item.func) != "Depends"
        })
        exceptions = sorted({
            ast.unparse(item.exc.func if isinstance(item.exc, ast.Call) else item.exc)
            for item in ast.walk(node)
            if isinstance(item, ast.Raise) and item.exc is not None
        })
        return FunctionDescription(
            name=node.name,
            qualified_name=qualified,
            module=qualified.rsplit(".", 2)[0] if parent else qualified.rsplit(".", 1)[0],
            owner_class=parent,
            file=file,
            line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            parameters=[item.arg for item in args],
            return_type=(
                ast.unparse(node.returns) if node.returns is not None else None
            ),
            decorators=[ast.unparse(item) for item in node.decorator_list],
            calls=calls,
            exceptions=exceptions,
            sqlalchemy_model_usage=cls._sqlalchemy_usage(node),
            side_effects=cls._side_effects(node),
            security_findings=cls._related_findings(findings, file, node),
        )

    @staticmethod
    def _constructor_dependencies(
        methods: list[ast.FunctionDef | ast.AsyncFunctionDef],
    ) -> list[str]:
        constructor = next((item for item in methods if item.name == "__init__"), None)
        if constructor is None:
            return []
        return [
            item.arg
            for item in [
                *constructor.args.posonlyargs,
                *constructor.args.args,
                *constructor.args.kwonlyargs,
            ]
            if item.arg not in {"self", "cls"}
        ]

    @staticmethod
    def _side_effects(node: ast.AST) -> list[str]:
        markers = {
            "add": "database_write", "delete": "database_write",
            "commit": "database_commit", "rollback": "database_rollback",
            "write": "filesystem_write", "unlink": "filesystem_delete",
            "send": "external_message", "publish": "external_message",
        }
        return sorted({
            markers[item.func.attr]
            for item in ast.walk(node)
            if isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and item.func.attr in markers
        })

    @staticmethod
    def _symbol(
        name: str,
        qualified: str,
        kind: str,
        file: str,
        node: ast.AST,
        parent: str | None = None,
    ) -> SymbolDescription:
        return SymbolDescription(
            name=name,
            qualified_name=qualified,
            kind=kind,
            file=file,
            line=node.lineno,
            end_line=getattr(node, "end_lineno", None) or node.lineno,
            parent=parent,
        )

    @staticmethod
    def _calls(
        node: FunctionNode, caller: str, file: str
    ) -> list[CallGraphEdge]:
        return [
            CallGraphEdge(
                caller=caller,
                callee=ast.unparse(item.func),
                file=file,
                line=item.lineno,
            )
            for statement in node.body
            for item in ast.walk(statement)
            if isinstance(item, ast.Call)
            and CodeUnderstandingAgent._call_name(item.func) != "Depends"
        ]

    @classmethod
    def _build_call_graph(
        cls, parsed, module_names: dict[str, str]
    ) -> list[CallGraphEdge]:
        edges = []
        for source, tree in parsed:
            module = module_names[source.path]
            local_symbols = {
                node.name: f"{module}.{node.name}"
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            }
            bindings = cls._import_bindings(
                source.path, tree, module=module
            )

            def add_calls(
                statements: list[ast.stmt],
                caller: str,
                current_class: str | None = None,
            ) -> None:
                visitor = _RuntimeAstVisitor()
                for statement in statements:
                    visitor.visit(statement)
                for call in visitor.calls:
                    if cls._excluded_runtime_call(call):
                        continue
                    edges.append(CallGraphEdge(
                        caller=caller,
                        callee=cls._resolve_call(
                            call.func,
                            bindings,
                            local_symbols,
                            current_class,
                        ),
                        file=source.path,
                        line=call.lineno,
                    ))

            module_statements = [
                statement for statement in tree.body
                if not isinstance(statement, (
                    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                    ast.Import, ast.ImportFrom,
                ))
            ]
            add_calls(module_statements, module)
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    add_calls(node.body, f"{module}.{node.name}")
                elif isinstance(node, ast.ClassDef):
                    class_name = f"{module}.{node.name}"
                    for method in node.body:
                        if isinstance(method, (
                            ast.FunctionDef, ast.AsyncFunctionDef
                        )):
                            add_calls(
                                method.body,
                                f"{class_name}.{method.name}",
                                class_name,
                            )
        return edges

    @classmethod
    def _import_bindings(
        cls, file: str, tree: ast.Module, *, module: str | None = None
    ) -> dict[str, str]:
        bindings = {}
        module = module or cls._module_name(file)
        package = module if file.replace("\\", "/").endswith(
            "/__init__.py"
        ) else module.rsplit(".", 1)[0] if "." in module else ""
        for statement in tree.body:
            if isinstance(statement, ast.Import):
                for alias in statement.names:
                    local = alias.asname or alias.name.split(".")[0]
                    bindings[local] = (
                        alias.name if alias.asname else alias.name.split(".")[0]
                    )
            elif isinstance(statement, ast.ImportFrom):
                imported_module = statement.module or ""
                if statement.level:
                    parts = package.split(".") if package else []
                    parts = parts[
                        :max(0, len(parts) - statement.level + 1)
                    ]
                    imported_module = ".".join([
                        *parts,
                        *([imported_module] if imported_module else []),
                    ])
                for alias in statement.names:
                    bindings[alias.asname or alias.name] = ".".join(
                        filter(None, [imported_module, alias.name])
                    )
        return bindings

    @classmethod
    def _resolve_call(
        cls,
        node: ast.AST,
        bindings: dict[str, str],
        local_symbols: dict[str, str],
        current_class: str | None,
    ) -> str:
        if isinstance(node, ast.Name):
            return bindings.get(
                node.id, local_symbols.get(node.id, node.id)
            )
        if isinstance(node, ast.Attribute):
            if (
                isinstance(node.value, ast.Name)
                and node.value.id in {"self", "cls"}
                and current_class is not None
            ):
                return f"{current_class}.{node.attr}"
            base = cls._resolve_reference(
                node.value, bindings, local_symbols
            )
            return f"{base}.{node.attr}"
        return ast.unparse(node)

    @classmethod
    def _resolve_reference(
        cls,
        node: ast.AST,
        bindings: dict[str, str],
        local_symbols: dict[str, str],
    ) -> str:
        if isinstance(node, ast.Name):
            return bindings.get(
                node.id, local_symbols.get(node.id, node.id)
            )
        if isinstance(node, ast.Attribute):
            return (
                f"{cls._resolve_reference(node.value, bindings, local_symbols)}"
                f".{node.attr}"
            )
        if isinstance(node, ast.Call):
            return cls._resolve_call(
                node.func, bindings, local_symbols, None
            ) + "()"
        return ast.unparse(node)

    @classmethod
    def _excluded_runtime_call(cls, call: ast.Call) -> bool:
        name = CodeUnderstandingAgent._call_name(call.func)
        if name == "Depends":
            return True
        if not isinstance(call.func, ast.Attribute):
            return False
        root = call.func.value
        while isinstance(root, ast.Attribute):
            root = root.value
        return (
            name in cls._HTTP_METHODS
            and isinstance(root, ast.Name)
            and root.id.casefold().endswith("router")
        )

    @classmethod
    def _sqlalchemy_usage(cls, node: ast.AST) -> list[str]:
        usage = set()
        session_names = {"db", "session"}
        is_model_class = (
            isinstance(node, ast.ClassDef)
            and any(
                CodeUnderstandingAgent._call_name(base)
                in {"Base", "DeclarativeBase"}
                for base in node.bases
            )
        )
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for argument in [
                *node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs
            ]:
                annotation = (
                    ast.unparse(argument.annotation)
                    if argument.annotation is not None else ""
                )
                if "Session" in annotation:
                    session_names.add(argument.arg)
        for item in ast.walk(node):
            if isinstance(item, (ast.Assign, ast.AnnAssign)):
                value = item.value
                if (
                    isinstance(value, ast.Call)
                    and CodeUnderstandingAgent._call_name(value.func)
                    == "SessionLocal"
                ):
                    targets = (
                        item.targets if isinstance(item, ast.Assign)
                        else [item.target]
                    )
                    session_names.update(
                        target.id for target in targets
                        if isinstance(target, ast.Name)
                    )
                    usage.add("SessionLocal()")
            if isinstance(item, ast.Call):
                name = CodeUnderstandingAgent._call_name(item.func)
                if name == "SessionLocal":
                    usage.add("SessionLocal()")
                elif (
                    isinstance(item.func, ast.Attribute)
                    and name in {
                        *cls._SQLALCHEMY_CALLS,
                        "close",
                    }
                    and cls._session_receiver(
                        item.func.value, session_names
                    )
                ):
                    usage.add(ast.unparse(item.func))
                    usage.update(
                        ast.unparse(argument) for argument in item.args
                        if (
                            isinstance(argument, ast.Name)
                            and argument.id[:1].isupper()
                        ) or (
                            isinstance(argument, ast.Attribute)
                            and argument.attr[:1].isupper()
                        )
                    )
                elif is_model_class and name in {
                    "Column", "mapped_column", "relationship",
                    "ForeignKey", "Index", "UniqueConstraint",
                    "CheckConstraint",
                }:
                    usage.add(name)
            if isinstance(item, (ast.Yield, ast.YieldFrom)):
                yielded = item.value
                if isinstance(yielded, ast.Name) and yielded.id in session_names:
                    usage.add(f"yield {yielded.id}")
            if isinstance(item, ast.ClassDef):
                for base in item.bases:
                    name = CodeUnderstandingAgent._call_name(base)
                    if name in {"Base", "DeclarativeBase"}:
                        usage.add(name)
        return sorted(usage)

    @classmethod
    def _session_receiver(
        cls, node: ast.AST, session_names: set[str]
    ) -> bool:
        if isinstance(node, ast.Name):
            return (
                node.id in session_names
                or node.id.endswith("_session")
                or node.id.endswith("_db")
            )
        if isinstance(node, ast.Attribute):
            return cls._session_receiver(node.value, session_names)
        if isinstance(node, ast.Call):
            if CodeUnderstandingAgent._call_name(node.func) == "SessionLocal":
                return True
            if isinstance(node.func, ast.Attribute):
                return cls._session_receiver(node.func.value, session_names)
        return False

    @classmethod
    def _related_findings(
        cls,
        findings: list[SecurityFindingDescription],
        file: str,
        node: ast.AST,
    ) -> list[SecurityFindingDescription]:
        decorators = getattr(node, "decorator_list", [])
        start = min(
            [getattr(node, "lineno", 0), *[
                item.lineno for item in decorators
                if hasattr(item, "lineno")
            ]]
        )
        end = getattr(node, "end_lineno", start) or start
        return [
            item for item in findings
            if cls._same_path(item.file, file) and start <= item.line <= end
        ]

    @staticmethod
    def _same_path(left: str, right: str) -> bool:
        return left.replace("\\", "/").lstrip("./") == right.replace(
            "\\", "/"
        ).lstrip("./")

    @classmethod
    def _endpoints(
        cls,
        parsed,
        functions: list[FunctionDescription],
        classes: list[ClassDescription],
        findings: list[SecurityFindingDescription],
    ) -> list[ApiEndpointDescription]:
        raw = CodeUnderstandingAgent._source_endpoints(
            CodeUnderstandingContext(
                project_id="00000000-0000-0000-0000-000000000000",
                dependency_run_id="00000000-0000-0000-0000-000000000000",
                files=[source for source, _ in parsed],
            )
        )
        function_lookup = {(item.file, item.name): item for item in functions}
        result = []
        for (method, route, handler, file), fact in raw.items():
            function = function_lookup.get((file, handler))
            result.append(ApiEndpointDescription(
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
                security_findings=(
                    function.security_findings if function else []
                ),
            ))
        return sorted(result, key=lambda item: (item.file, item.route, item.method))

    @staticmethod
    def _entrypoints(context, endpoints):
        result = [
            EntrypointDescription(
                path=item.path,
                symbol=item.functions[0] if item.functions else None,
                purpose="Application entrypoint",
            )
            for item in context.files if item.is_entry_point
        ]
        for endpoint in endpoints:
            if not any(
                item.path == endpoint.file and item.symbol == endpoint.handler
                for item in result
            ):
                result.append(EntrypointDescription(
                    path=endpoint.file,
                    symbol=endpoint.handler,
                    purpose="API endpoint",
                ))
        return result

    @staticmethod
    def _class_node(parsed, file, name):
        return next(
            (
                node for source, tree in parsed if source.path == file
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == name
            ),
            None,
        )

    @classmethod
    def _class_fields(cls, parsed, file, name) -> list[str]:
        node = cls._class_node(parsed, file, name)
        if node is None:
            return []
        result = []
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                result.append(item.target.id)
            elif isinstance(item, ast.Assign):
                result.extend(
                    target.id for target in item.targets
                    if isinstance(target, ast.Name)
                )
        return result

    @classmethod
    def _class_relationships(cls, parsed, file, name) -> list[str]:
        node = cls._class_node(parsed, file, name)
        if node is None:
            return []
        return sorted({
            ast.unparse(item)
            for item in ast.walk(node)
            if isinstance(item, ast.Call)
            and CodeUnderstandingAgent._call_name(item.func)
            in {"relationship", "ForeignKey"}
        })

    @classmethod
    def _sqlalchemy_model_metadata(
        cls, node: ast.ClassDef | None
    ) -> dict[str, list]:
        result: dict[str, list] = {
            "columns": [],
            "primary_keys": [],
            "foreign_keys": [],
            "relationships": [],
            "constraints": [],
            "indexes": [],
            "unique_constraints": [],
            "check_constraints": [],
        }
        if node is None:
            return result

        for statement in node.body:
            target = None
            annotation = None
            value = None
            if isinstance(statement, ast.AnnAssign) and isinstance(
                statement.target, ast.Name
            ):
                target = statement.target.id
                annotation = statement.annotation
                value = statement.value
            elif isinstance(statement, ast.Assign):
                target = next(
                    (
                        item.id for item in statement.targets
                        if isinstance(item, ast.Name)
                    ),
                    None,
                )
                value = statement.value

            if target == "__table_args__":
                cls._table_constraints(value, result)
                continue
            if target is None or not isinstance(value, ast.Call):
                continue
            call_name = CodeUnderstandingAgent._call_name(value.func)
            if call_name == "relationship":
                result["relationships"].append(
                    f"{target} = {ast.unparse(value)}"
                )
                continue
            if call_name not in {"Column", "mapped_column"}:
                continue

            primary_key = cls._bool_keyword(value, "primary_key", False)
            nullable = cls._optional_bool_keyword(value, "nullable")
            if nullable is None and primary_key:
                nullable = False
            foreign_keys = [
                (
                    str(CodeUnderstandingAgent._literal(argument.args[0]))
                    if argument.args
                    and CodeUnderstandingAgent._literal(argument.args[0])
                    is not None
                    else ast.unparse(
                        argument.args[0] if argument.args else argument
                    )
                )
                for argument in value.args
                if isinstance(argument, ast.Call)
                and CodeUnderstandingAgent._call_name(argument.func)
                == "ForeignKey"
            ]
            column_type = next(
                (
                    ast.unparse(argument)
                    for argument in value.args
                    if not (
                        isinstance(argument, ast.Call)
                        and CodeUnderstandingAgent._call_name(argument.func)
                        in {"ForeignKey", "CheckConstraint"}
                    )
                ),
                cls._mapped_annotation_type(annotation),
            )
            default_node = next(
                (
                    keyword.value for keyword in value.keywords
                    if keyword.arg in {"default", "server_default"}
                ),
                None,
            )
            default = CodeUnderstandingAgent._literal(default_node)
            if default_node is not None and default is None:
                default = ast.unparse(default_node)
            column = SQLAlchemyColumnDescription(
                name=target,
                type=column_type,
                primary_key=primary_key,
                foreign_keys=foreign_keys,
                nullable=nullable,
                default=default,
                index=cls._bool_keyword(value, "index", False),
                unique=cls._bool_keyword(value, "unique", False),
            )
            result["columns"].append(column)
            if column.primary_key:
                result["primary_keys"].append(target)
            result["foreign_keys"].extend(
                f"{target} -> {foreign_key}"
                for foreign_key in foreign_keys
            )
            if column.index:
                result["indexes"].append(target)
            if column.unique:
                result["unique_constraints"].append(target)
            for argument in value.args:
                if (
                    isinstance(argument, ast.Call)
                    and CodeUnderstandingAgent._call_name(argument.func)
                    == "CheckConstraint"
                ):
                    rendered = ast.unparse(argument)
                    result["check_constraints"].append(rendered)

        result["constraints"] = list(dict.fromkeys([
            *result["foreign_keys"],
            *result["unique_constraints"],
            *result["check_constraints"],
        ]))
        for key in result:
            if key != "columns":
                result[key] = list(dict.fromkeys(result[key]))
        return result

    @classmethod
    def _table_constraints(cls, value: ast.AST | None, result: dict) -> None:
        if value is None:
            return
        for item in ast.walk(value):
            if not isinstance(item, ast.Call):
                continue
            name = CodeUnderstandingAgent._call_name(item.func)
            rendered = ast.unparse(item)
            if name == "Index":
                result["indexes"].append(rendered)
            elif name == "UniqueConstraint":
                result["unique_constraints"].append(rendered)
            elif name == "CheckConstraint":
                result["check_constraints"].append(rendered)

    @staticmethod
    def _bool_keyword(call: ast.Call, name: str, default: bool) -> bool:
        value = PythonStaticAnalyzer._optional_bool_keyword(call, name)
        return default if value is None else value

    @staticmethod
    def _optional_bool_keyword(call: ast.Call, name: str) -> bool | None:
        return next(
            (
                keyword.value.value
                for keyword in call.keywords
                if keyword.arg == name
                and isinstance(keyword.value, ast.Constant)
                and isinstance(keyword.value.value, bool)
            ),
            None,
        )

    @staticmethod
    def _mapped_annotation_type(annotation: ast.AST | None) -> str | None:
        if isinstance(annotation, ast.Subscript):
            name = CodeUnderstandingAgent._call_name(annotation.value)
            if name == "Mapped":
                return ast.unparse(annotation.slice)
        return None

    @staticmethod
    def _session_factories(parsed) -> list[SQLAlchemySessionFactoryDescription]:
        factories = []
        for source, tree in parsed:
            for statement in tree.body:
                if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
                    continue
                value = statement.value
                if not isinstance(value, ast.Call):
                    continue
                factory = CodeUnderstandingAgent._call_name(value.func)
                if factory not in {"sessionmaker", "async_sessionmaker"}:
                    continue
                targets = (
                    statement.targets
                    if isinstance(statement, ast.Assign)
                    else [statement.target]
                )
                bind = next(
                    (
                        ast.unparse(keyword.value)
                        for keyword in value.keywords
                        if keyword.arg == "bind"
                    ),
                    None,
                )
                factories.extend(
                    SQLAlchemySessionFactoryDescription(
                        name=target.id,
                        file=source.path,
                        factory=factory,
                        bind=bind,
                    )
                    for target in targets if isinstance(target, ast.Name)
                )
        return sorted(factories, key=lambda item: (item.file, item.name))

    @staticmethod
    def _business_rules(parsed) -> list[BusinessRuleDescription]:
        result = []
        for source, tree in parsed:
            for node in ast.walk(tree):
                if isinstance(node, ast.If):
                    result.append(BusinessRuleDescription(
                        description=f"Condition: {ast.unparse(node.test)}",
                        files=[source.path],
                    ))
        return result
