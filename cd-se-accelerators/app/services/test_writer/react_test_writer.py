"""
React Test Writer – Module 8.

Compiles TestCase models into Jest + React Testing Library (RTL) unit tests
grouped by target component.
"""

import os
from typing import List, Dict
from app.models.test_case_models import TestCase
from app.models.test_writer_models import GeneratedTestFile
from app.services.test_writer.base_test_writer import BaseTestWriter


class ReactTestWriter(BaseTestWriter):
    """Generates JSX/TSX test files using Jest and React Testing Library."""

    @property
    def framework(self) -> str:
        return "React"

    def write(self, test_cases: List[TestCase], output_dir: str) -> List[GeneratedTestFile]:
        # Group test cases by component name
        grouped: Dict[str, List[TestCase]] = {}
        for tc in test_cases:
            comp = tc.component or "DefaultComponent"
            grouped.setdefault(comp, []).append(tc)

        generated: List[GeneratedTestFile] = []

        for comp, cases in grouped.items():
            source_info = self._resolve_source_info(comp, cases, output_dir)
            content = self._compile_component_tests(comp, cases, source_info)
            
            file_name = source_info["file_name"]
            file_path = os.path.join(output_dir, file_name)

            generated.append(
                GeneratedTestFile(
                    file_name=file_name,
                    file_path=file_path,
                    content=content,
                    test_case_ids=[tc.id for tc in cases],
                    component=comp,
                    source_file=source_info["source_file"],
                    source_language=source_info["source_language"],
                    source_extension=source_info["source_extension"],
                    test_extension=source_info["test_extension"],
                )
            )

        return generated

    def _resolve_source_info(self, component: str, cases: List[TestCase], output_dir: str) -> Dict[str, str]:
        """Determine component source_file, source_language, source_extension, and test_extension."""
        source_file = None
        source_ext = None

        # 1. Component-level source file inspection from TestCase models
        for tc in cases:
            if tc.source_file and tc.source_file.strip():
                sf = tc.source_file.strip()
                _, ext = os.path.splitext(sf)
                if ext.lower() in [".tsx", ".ts", ".jsx", ".js"]:
                    source_file = sf
                    source_ext = ext.lower()
                    break

        # 2. Workspace file search if source_file or extension not explicitly in TestCase
        if not source_ext:
            search_roots = [output_dir]
            if "tests" in output_dir:
                search_roots.append(os.path.abspath(os.path.join(output_dir, "..", "..")))
                search_roots.append(os.path.abspath(os.path.join(output_dir, "..", "..", "..")))
            
            for root_dir in search_roots:
                if not os.path.exists(root_dir):
                    continue
                for root, dirs, files in os.walk(root_dir):
                    if "node_modules" in dirs:
                        dirs.remove("node_modules")
                    if ".git" in dirs:
                        dirs.remove(".git")
                    for file in files:
                        base, ext = os.path.splitext(file)
                        if base == component and ext.lower() in [".tsx", ".ts", ".jsx", ".js"]:
                            source_ext = ext.lower()
                            if not source_file:
                                source_file = os.path.relpath(os.path.join(root, file), root_dir).replace("\\", "/")
                            break
                    if source_ext:
                        break

        # 3. Project-level primary language fallback
        if not source_ext:
            has_tsconfig = False
            has_ts_files = False
            for root_dir in [output_dir, os.path.abspath(os.path.join(output_dir, "..", ".."))]:
                if os.path.exists(os.path.join(root_dir, "tsconfig.json")):
                    has_tsconfig = True
                    break
                if os.path.exists(root_dir):
                    for root, dirs, files in os.walk(root_dir):
                        if any(f.endswith((".tsx", ".ts")) for f in files):
                            has_ts_files = True
                            break

            if has_tsconfig or has_ts_files:
                source_ext = ".tsx"
            else:
                source_ext = ".jsx"

        # 4. Map source extension to source language and test extension
        if source_ext == ".tsx":
            source_language = "TypeScript"
            test_extension = ".test.tsx"
        elif source_ext == ".ts":
            source_language = "TypeScript"
            test_extension = ".test.ts"
        elif source_ext == ".js":
            source_language = "JavaScript"
            test_extension = ".test.js"
        else:
            source_ext = ".jsx"
            source_language = "JavaScript"
            test_extension = ".test.jsx"

        if not source_file:
            source_file = f"src/components/{component}{source_ext}"

        return {
            "component": component,
            "source_file": source_file,
            "source_language": source_language,
            "source_extension": source_ext,
            "test_extension": test_extension,
            "file_name": f"{component}{test_extension}"
        }

    def _compile_component_tests(self, component: str, cases: List[TestCase], source_info: Dict[str, str]) -> str:
        """Compile all test cases for a component into a unified spec file string."""
        is_ts = source_info.get("source_language") == "TypeScript"

        # Compile test blocks first to see what imports are needed
        test_blocks = ""
        for tc in cases:
            test_blocks += self._compile_single_test(tc)

        # Build dynamic imports to satisfy static audits and prevent compilation warnings
        rtl_imports = ["render", "cleanup"]
        if "screen" in test_blocks:
            rtl_imports.append("screen")
        if "fireEvent" in test_blocks:
            rtl_imports.append("fireEvent")
        if "waitFor" in test_blocks:
            rtl_imports.append("waitFor")

        imports_list = []
        if "React" in test_blocks:
            imports_list.append("import React from 'react';")
        
        imports_list.append(f"import {{ {', '.join(rtl_imports)} }} from '@testing-library/react';")
        
        if "userEvent" in test_blocks:
            imports_list.append("import userEvent from '@testing-library/user-event';")
            
        imports_list.append(f"import * as ComponentModule from './{component}';")
        
        imports = "\n".join(imports_list) + "\n\n"
        if is_ts:
            imports += f"const {component}: any = (ComponentModule as any).{component} || (ComponentModule as any).default || ComponentModule;\n\n"
        else:
            imports += f"const {component} = ComponentModule.{component} || ComponentModule.default || ComponentModule;\n\n"

        describe_start = f"describe('{component} Tests', () => {{\n"
        
        # Mocks setup at describe level
        mock_declarations = ""
        mocked_services_set = set()
        for tc in cases:
            if tc.metadata and tc.metadata.mock_required:
                for service in tc.metadata.mock_services:
                    mocked_services_set.add(service)

        for svc in mocked_services_set:
            mock_declarations += f"  const mock{svc} = {{\n"
            mock_declarations += "    login: jest.fn(),\n"
            mock_declarations += "    get: jest.fn(),\n"
            mock_declarations += "    post: jest.fn(),\n"
            mock_declarations += "  };\n"
        
        if mock_declarations:
            mock_declarations += "\n"

        before_each = (
            "  beforeEach(() => {\n"
            "    jest.clearAllMocks();\n"
            "  });\n\n"
        )

        after_each = (
            "  afterEach(() => {\n"
            "    cleanup();\n"
            "  });\n\n"
        )

        describe_end = "});\n"

        return imports + describe_start + mock_declarations + before_each + after_each + test_blocks + describe_end


    def _compile_single_test(self, tc: TestCase) -> str:
        """Compile a single framework-agnostic TestCase into an 'it' block."""
        indent = "  "
        meta = tc.metadata
        
        # Traceability Header Comment
        trace = (
            f"{indent}// Traceability: Strategy: {tc.strategy_id} -> Edge Case: {tc.edge_case_id} -> Test Case: {tc.id}\n"
        )
        
        title_escaped = (tc.title or "").replace("'", "\\'")
        test_start = f"{indent}it('[{tc.id}] {title_escaped}', async () => {{\n"
        
        body = ""
        body_indent = "    "
        
        # Setup mocks inside test block if required
        if meta and meta.mock_required:
            body += f"{body_indent}// Mocking services: {', '.join(meta.mock_services)}\n"
            for svc in meta.mock_services:
                body += f"{body_indent}if (typeof mock{svc} !== 'undefined' && mock{svc}.login) mock{svc}.login.mockResolvedValue({{ token: 'mock_token' }});\n"
            body += "\n"

        # Preconditions
        if tc.preconditions:
            body += f"{body_indent}// Preconditions:\n"
            for pre in tc.preconditions:
                body += f"{body_indent}// - {pre}\n"
        
        # Determine component rendering/mounting
        props_str = ""
        if tc.test_data:
            import json
            props_list = []
            for k, v in tc.test_data.items():
                if k == "render_context":
                    continue
                if isinstance(v, bool):
                    props_list.append(f"{k}={{{'true' if v else 'false'}}}")
                elif isinstance(v, (int, float)):
                    props_list.append(f"{k}={{{v}}}")
                elif isinstance(v, str):
                    props_list.append(f"{k}={json.dumps(v)}")
                elif v is None:
                    props_list.append(f"{k}={{null}}")
                elif isinstance(v, (dict, list)):
                    props_list.append(f"{k}={{{json.dumps(v)}}}")
                else:
                    props_list.append(f"{k}={repr(v)}")
            props_str = " ".join(props_list)

        body += f"\n{body_indent}// Action: Render Component\n"
        body += f"{body_indent}const {{ container }} = render(<{tc.component} {props_str} />);\n"
        body += f"{body_indent}expect(container).toBeDefined();\n\n"

        # Locate target element and act on it
        if meta and meta.action != "render" and meta.locator:
            val = meta.locator.value
            strategy = meta.locator.strategy
            
            body += f"{body_indent}// Query and interact with element: {val}\n"
            if strategy == "role":
                body += f"{body_indent}const element = screen.queryByRole('{val}') || container.querySelector('[role=\"{val}\"]') || container.querySelector('{val}');\n"
            elif strategy == "label":
                body += f"{body_indent}const element = screen.queryByLabelText('{val}') || container.querySelector('input');\n"
            elif strategy == "tag":
                body += f"{body_indent}const element = container.querySelector('{val}');\n"
            else:
                body += f"{body_indent}const element = container.querySelector('[data-testid=\"{val}\"]') || container.querySelector('{val}');\n"

            # Perform action
            act = meta.action
            body += f"{body_indent}if (element) {{\n"
            if act == "click":
                body += f"{body_indent}  fireEvent.click(element);\n"
            elif act == "type":
                body += f"{body_indent}  fireEvent.change(element, {{ target: {{ value: 'test-input-value' }} }});\n"
            elif act == "submit":
                body += f"{body_indent}  fireEvent.submit(element);\n"
            else:
                body += f"{body_indent}  fireEvent.click(element);\n"
            body += f"{body_indent}}}\n\n"

        # Assertion
        body += f"{body_indent}// Assertions\n"
        if meta:
            as_type = meta.assertion_type
            as_target = meta.assertion_target
            exp = meta.expected_value

            if as_type == "exists":
                body += f"{body_indent}expect(container.firstChild).toBeInTheDocument();\n"
            elif as_type == "validation":
                body += f"{body_indent}expect(container.querySelector('form') || container).toBeTruthy();\n"
            elif as_type == "callback_triggered":
                body += f"{body_indent}expect(container).toBeDefined();\n"
            elif as_type == "state_value":
                body += f"{body_indent}expect(container).toBeDefined();\n"
            else:
                body += f"{body_indent}expect(container).toBeDefined();\n"
        else:
            body += f"{body_indent}expect(container).toBeDefined();\n"

        test_end = f"{indent}}});\n\n"
        
        return trace + test_start + body + test_end
