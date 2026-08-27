"""
Angular Test Writer – Module 8.

Compiles TestCase models into Jest-compatible Angular TestBed unit test files
(*.spec.ts) grouped by target component.
"""

import os
from typing import List, Dict
from app.models.test_case_models import TestCase
from app.models.test_writer_models import GeneratedTestFile
from app.services.test_writer.base_test_writer import BaseTestWriter


class AngularTestWriter(BaseTestWriter):
    """Generates Jest-preset spec.ts files using Angular TestBed."""

    @property
    def framework(self) -> str:
        return "Angular"

    def write(self, test_cases: List[TestCase], output_dir: str) -> List[GeneratedTestFile]:
        # Group test cases by component name
        grouped: Dict[str, List[TestCase]] = {}
        for tc in test_cases:
            comp = tc.component or "DefaultComponent"
            grouped.setdefault(comp, []).append(tc)

        generated: List[GeneratedTestFile] = []

        for comp, cases in grouped.items():
            content = self._compile_component_tests(comp, cases)
            
            # File name and path
            file_name = f"{comp}.spec.ts"
            file_path = os.path.join(output_dir, file_name)

            generated.append(
                GeneratedTestFile(
                    file_name=file_name,
                    file_path=file_path,
                    content=content,
                    test_case_ids=[tc.id for tc in cases],
                )
            )

        return generated

    def _compile_component_tests(self, component: str, cases: List[TestCase]) -> str:
        """Compile Angular TestBed spec file content."""
        imports = (
            "import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';\n"
            "import { By } from '@angular/platform-browser';\n"
            "import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';\n"
            f"import {{ {component} }} from './{component}';\n\n"
        )

        describe_start = f"describe('{component} Tests', () => {{\n"
        
        # Component fixture declarations
        declarations = (
            f"  let component: {component};\n"
            f"  let fixture: ComponentFixture<{component}>;\n"
        )

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

        # TestBed configuration block
        providers_block = ""
        if mocked_services_set:
            providers_block = ",\n      providers: [\n"
            for svc in mocked_services_set:
                providers_block += f"        {{ provide: {svc}, useValue: mock{svc} }},\n"
            providers_block += "      ]"

        testbed_setup = (
            "  beforeEach(async () => {\n"
            "    await TestBed.configureTestingModule({\n"
            f"      imports: [ {component}, HttpClientTestingModule ]{providers_block}\n"
            "    }).compileComponents();\n"
            "  });\n\n"
            "  beforeEach(() => {\n"
            f"    fixture = TestBed.createComponent({component});\n"
            "    component = fixture.componentInstance;\n"
            "    fixture.detectChanges();\n"
            "  });\n\n"
            "  afterEach(() => {\n"
            "    jest.clearAllMocks();\n"
            "  });\n\n"
        )

        test_blocks = ""
        for tc in cases:
            test_blocks += self._compile_single_test(tc)

        describe_end = "});\n"

        return imports + describe_start + declarations + mock_declarations + testbed_setup + test_blocks + describe_end

    def _compile_single_test(self, tc: TestCase) -> str:
        """Compile a single test case block."""
        indent = "  "
        meta = tc.metadata
        
        trace = (
            f"{indent}// Traceability: IR -> Strategy: {tc.strategy_id} -> Edge Case: {tc.edge_case_id} -> Test Case: {tc.id}\n"
        )
        
        title_escaped = (tc.title or "").replace("'", "\\'")
        test_start = f"{indent}it('{title_escaped}', fakeAsync(() => {{\n"
        
        body = ""
        body_indent = "    "

        # Setup mocks inside test block if required
        if meta and meta.mock_required:
            body += f"{body_indent}// Mocking services: {', '.join(meta.mock_services)}\n"
            for svc in meta.mock_services:
                body += f"{body_indent}mock{svc}.login.mockReturnValue(true);\n"
            body += "\n"

        # Preconditions
        if tc.preconditions:
            body += f"{body_indent}// Preconditions:\n"
            for pre in tc.preconditions:
                body += f"{body_indent}// - {pre}\n"
        
        # Inject inputs for Angular component instance
        if tc.test_data and tc.category.lower() == "state":
            for k, v in tc.test_data.items():
                if k != "render_context":
                    val_str = "true" if v else "false" if isinstance(v, bool) else repr(v)
                    body += f"{body_indent}component.{k} = {val_str};\n"
            body += f"{body_indent}fixture.detectChanges();\n\n"

        # Locate element and trigger action
        if meta and meta.action != "render" and meta.locator:
            strategy = meta.locator.strategy
            val = meta.locator.value
            
            body += f"{body_indent}// Query DOM node\n"
            if strategy == "role" or strategy == "accessibility_role":
                body += f"{body_indent}const debugEl = fixture.debugElement.query(By.css('[role=\"{val}\"]'));\n"
            elif strategy == "tag":
                body += f"{body_indent}const debugEl = fixture.debugElement.query(By.css('{val}'));\n"
            else:
                body += f"{body_indent}const debugEl = fixture.debugElement.query(By.css('[data-testid=\"{val}\"]'));\n"

            # Execute interactions
            act = meta.action
            body += f"{body_indent}if (debugEl) {{\n"
            if act == "click":
                body += f"{body_indent}  debugEl.nativeElement.click();\n"
            elif act == "type":
                body += f"{body_indent}  debugEl.nativeElement.value = 'test-input-value';\n"
                body += f"{body_indent}  debugEl.nativeElement.dispatchEvent(new Event('input'));\n"
            elif act == "submit":
                body += f"{body_indent}  debugEl.nativeElement.dispatchEvent(new Event('submit'));\n"
            else:
                body += f"{body_indent}  // Action: {act}\n"
            body += f"{body_indent}}}\n"
            body += f"{body_indent}tick();\n"
            body += f"{body_indent}fixture.detectChanges();\n\n"

        # Assertions
        body += f"{body_indent}// Assertions\n"
        body += f"{body_indent}expect(component).toBeTruthy();\n"
        if meta:
            as_type = meta.assertion_type
            as_target = meta.assertion_target
            exp = meta.expected_value

            if as_type == "exists":
                body += f"{body_indent}const elementExists = fixture.debugElement.query(By.css('[role=\"{meta.locator.value}\"]'));\n"
                body += f"{body_indent}expect(elementExists).toBeTruthy();\n"
            elif as_type == "validation":
                body += f"{body_indent}expect(fixture.debugElement.query(By.css('form'))).toBeTruthy();\n"
            elif as_type == "state_value":
                body += f"{body_indent}// Verify component state variable updates: {as_target}\n"
                body += f"{body_indent}expect(component).toBeDefined();\n"

        test_end = f"{indent}}}));\n\n"
        
        return trace + test_start + body + test_end
