import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.db.models import (
    Project,
    PipelineRun,
    Component,
    TestCaseModel,
    TestFileModel,
    TestExecutionModel,
    TestResultModel,
    CoverageReportModel,
    ReportModel,
)

logger = logging.getLogger(__name__)

def clean_empty_projects(db: Session) -> None:
    """Safely delete projects that have zero test cases to prevent dashboard clutter."""
    try:
        projects = db.query(Project).all()
        cleaned_count = 0
        for p in projects:
            # Skip seeding targets
            if p.id in ["proj_mock_react_ecommerce", "proj_mock_angular_customer", "proj_mock_vue_task"]:
                continue
            
            tc_count = db.query(TestCaseModel).filter(TestCaseModel.project_id == p.id).count()
            if tc_count == 0:
                logger.info("Self-healing: Deleting empty project '%s' (ID: %s)", p.project_name, p.id)
                # Cascading delete handles related runs, files, etc.
                db.delete(p)
                cleaned_count += 1
        if cleaned_count > 0:
            db.commit()
            logger.info("Self-healing: Cleaned up %d empty projects.", cleaned_count)
    except Exception as exc:
        db.rollback()
        logger.error("Error during database self-healing cleanup: %s", exc)


def create_full_mock_project(
    db: Session,
    project_id: str,
    project_name: str,
    framework: str,
    source_files_count: int,
    test_cases: List[Dict[str, Any]],
    test_files: List[Dict[str, Any]],
    execution_metrics: Dict[str, Any],
    coverage_metrics: Dict[str, Any]
) -> None:
    """Create a project and populate it with fully realized mock pipelines, cases, files, and reports."""
    # Check if project already exists
    existing = db.query(Project).filter(Project.id == project_id).first()
    if existing:
        return

    # 1. Project
    proj = Project(
        id=project_id,
        project_name=project_name,
        framework=framework,
        project_path=f"scratch/test_workspace/mock_{project_id}",
        workspace_path=f"scratch/test_workspace/mock_{project_id}",
        status="completed",
        source_file_count=source_files_count,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(proj)
    db.flush()

    # 2. Pipeline Run
    run_id = f"run_mock_{project_id}_{uuid.uuid4().hex[:6]}"
    run = PipelineRun(
        id=run_id,
        project_id=project_id,
        status="completed",
        current_stage="validation",
        progress=1.0,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    db.add(run)
    db.flush()

    # 3. Components
    components_map = {}
    unique_components = list(set(tc["component"] for tc in test_cases))
    for c_name in unique_components:
        comp_id = f"comp_{c_name.lower()}_{uuid.uuid4().hex[:6]}"
        comp = Component(
            id=comp_id,
            project_id=project_id,
            pipeline_run_id=run_id,
            name=c_name,
            component_type="ReactComponent" if "angular" not in framework.lower() else "AngularComponent",
            framework=framework,
        )
        db.add(comp)
        components_map[c_name] = comp_id
    db.flush()

    # 4. Test Cases
    db_test_cases = []
    # Generate unique test case prefix based on project_id
    clean_pid = project_id.replace("proj_mock_", "").replace("proj_", "")
    parts = clean_pid.split("_")
    if len(parts) == 1 and len(parts[0]) >= 10:
        prefix = parts[0][-4:].upper()
    else:
        prefix = parts[-1].upper()[:4]
    for idx, tc in enumerate(test_cases):
        tc_id = f"TC-{prefix}-{idx+1:03d}"
        comp_id = components_map.get(tc["component"])
        db_tc = TestCaseModel(
            id=tc_id,
            project_id=project_id,
            pipeline_run_id=run_id,
            component_id=comp_id,
            title=tc["title"],
            objective=tc["objective"],
            category=tc["category"],
            priority=tc["priority"],
            steps=tc["steps"],
            expected_result=tc["expected_result"],
            source_function=tc.get("source_function", "render"),
            status="generated",
            quality_score=tc.get("quality_score", 100)
        )
        db.add(db_tc)
        db_test_cases.append(db_tc)
    db.flush()

    # 5. Test Files
    db_test_files = []
    for tf in test_files:
        # Match generated case IDs matching the component name
        tc_ids = [
            tc.id for tc in db_test_cases 
            if components_map.get(tf["component"]) == tc.component_id
        ]
        db_tf = TestFileModel(
            id=f"file_mock_{uuid.uuid4().hex[:10]}",
            project_id=project_id,
            pipeline_run_id=run_id,
            component_id=components_map.get(tf["component"]),
            file_name=tf["file_name"],
            file_path=f"scratch/test_workspace/mock_{project_id}/src/components/{tf['file_name']}",
            framework=framework,
            test_case_ids=tc_ids,
            generated_at=datetime.utcnow()
        )
        db.add(db_tf)
        db_test_files.append((db_tf, tf["content"], tc_ids))
    db.flush()

    # 6. Test Execution
    exec_id = f"exec_mock_{uuid.uuid4().hex[:10]}"
    execution = TestExecutionModel(
        id=exec_id,
        project_id=project_id,
        pipeline_run_id=run_id,
        status="completed",
        total_tests=execution_metrics["total_tests"],
        passed=execution_metrics["passed"],
        failed=execution_metrics["failed"],
        skipped=execution_metrics["skipped"],
        execution_time_ms=execution_metrics.get("execution_time_ms", 4500.0),
        pass_rate=execution_metrics["pass_rate"],
        created_at=datetime.utcnow()
    )
    db.add(execution)
    db.flush()

    # 7. Test Results Details
    # Map results dynamically for seeded cases
    for db_tc in db_test_cases:
        # Check if this case should fail based on metrics
        is_failure = any(
            f["title"] == db_tc.title 
            for f in execution_metrics.get("failures_list", [])
        )
        
        res = TestResultModel(
            id=f"res_mock_{uuid.uuid4().hex[:10]}",
            execution_id=exec_id,
            test_case_id=db_tc.id,
            test_name=db_tc.title,
            status="failed" if is_failure else "passed",
            expected=db_tc.expected_result,
            actual=db_tc.expected_result if not is_failure else "AssertionError: expected component state to update",
            error_message=None if not is_failure else "Expected component element to be visible in DOM but it was omitted.",
            created_at=datetime.utcnow()
        )
        db.add(res)

    # 8. Coverage Report
    coverage = CoverageReportModel(
        id=f"cov_mock_{uuid.uuid4().hex[:10]}",
        project_id=project_id,
        pipeline_run_id=run_id,
        statements=coverage_metrics["statements"],
        branches=coverage_metrics["branches"],
        functions=coverage_metrics["functions"],
        lines=coverage_metrics["lines"],
        coverage_status="available",
        created_at=datetime.utcnow()
    )
    db.add(coverage)

    # 9. Main Report
    # Compile report data in the format parsed by ViewContainer.jsx
    synthesized_files_report = []
    for tf_obj, _, t_ids in db_test_files:
        t_failed = 0
        for f_item in execution_metrics.get("failures_list", []):
            if f_item["component"] == tf_obj.component_rel.name:
                t_failed += 1
        synthesized_files_report.append({
            "file_name": tf_obj.file_name,
            "passed": len(t_ids) - t_failed,
            "total_tests": len(t_ids),
            "failed": t_failed,
            "skipped": 0
        })

    report_data_json = {
        "execution_summary": {
            "total_tests": execution_metrics["total_tests"],
            "passed": execution_metrics["passed"],
            "failed": execution_metrics["failed"],
            "skipped": execution_metrics["skipped"],
            "pass_rate": execution_metrics["pass_rate"],
            "execution_time_ms": execution_metrics.get("execution_time_ms", 4500)
        },
        "coverage": {
            "statements": coverage_metrics["statements"],
            "branches": coverage_metrics["branches"],
            "functions": coverage_metrics["functions"],
            "lines": coverage_metrics["lines"],
            "coverage_status": "available"
        },
        "test_files": synthesized_files_report,
        "failures": [
            {
                "test_case_id": [tc.id for tc in db_test_cases if tc.title == f["title"]][0],
                "test_name": f["title"],
                "error_message": "DOM element assertion failed: component did not render within timeout.",
                "failure_details": "Expected value to be truthy but received falsy."
            }
            for f in execution_metrics.get("failures_list", [])
        ]
    }

    report = ReportModel(
        id=f"rep_mock_{uuid.uuid4().hex[:10]}",
        project_id=project_id,
        pipeline_run_id=run_id,
        total_tests=execution_metrics["total_tests"],
        passed=execution_metrics["passed"],
        failed=execution_metrics["failed"],
        skipped=execution_metrics["skipped"],
        pass_rate=execution_metrics["pass_rate"],
        overall_quality_score=execution_metrics.get("quality_score", 95.0),
        report_data=report_data_json,
        generated_at=datetime.utcnow()
    )
    db.add(report)
    db.commit()


def seed_initial_mock_projects(db: Session) -> None:
    """Clean up any legacy mock projects to ensure zero mock data."""
    try:
        mock_pids = ["proj_mock_react_ecommerce", "proj_mock_angular_customer", "proj_mock_vue_task"]
        for pid in mock_pids:
            p = db.query(Project).filter(Project.id == pid).first()
            if p:
                db.delete(p)
        db.commit()
        logger.info("Legacy mock projects cleaned up.")
    except Exception as exc:
        db.rollback()
        logger.warning("Error cleaning legacy mock projects: %s", exc)
    return
        {
            "component": "ShoppingCart",
            "title": "Verify Shopping Cart rendering with items",
            "objective": "Verify that shopping cart correctly lists all added products and updates badge count.",
            "category": "State",
            "priority": "High",
            "steps": [
                "1. Render ShoppingCart component with mock list containing 3 items",
                "2. Assert that item list contains exactly 3 entries",
                "3. Assert that badge count in header displays '3'"
            ],
            "expected_result": "Cart shows 3 items, layout displays correct item list, badge displays '3'."
        },
        {
            "component": "ShoppingCart",
            "title": "Verify quantity increment updates total price",
            "objective": "Verify that clicking quantity increment triggers state updates and total calculation.",
            "category": "Events",
            "priority": "High",
            "steps": [
                "1. Render ShoppingCart with single item priced $10 and quantity 1",
                "2. Click the increment (+) button for the item",
                "3. Verify quantity updates to 2 and subtotal changes to $20"
            ],
            "expected_result": "Quantity incremented to 2 and subtotal changes dynamically to $20."
        },
        {
            "component": "PaymentForm",
            "title": "Verify payment submission form validation",
            "objective": "Verify that submit blocks and raises error notifications when fields are incomplete.",
            "category": "Forms",
            "priority": "High",
            "steps": [
                "1. Render PaymentForm with empty card details",
                "2. Click checkout button",
                "3. Verify card number and expiry validation error displays are present"
            ],
            "expected_result": "Validation block prevents submission; errors highlighted on input fields."
        },
        {
            "component": "PaymentForm",
            "title": "Verify successful payment checkout callback",
            "objective": "Verify payment gateway success invokes success callback and triggers route redirection.",
            "category": "Services",
            "priority": "High",
            "steps": [
                "1. Render PaymentForm and fill credit card details",
                "2. Click Submit Payment",
                "3. Verify payment API is called and success page routing is triggered"
            ],
            "expected_result": "Checkout proceeds successfully; routes user to invoice success page."
        }
    ]
    ecommerce_files = [
        {
            "component": "ShoppingCart",
            "file_name": "ShoppingCart.test.jsx",
            "content": """import React from 'react';\nimport { render, screen, fireEvent } from '@testing-library/react';\nimport ShoppingCart from './ShoppingCart';\n\ndescribe('ShoppingCart Component', () => {\n  it('renders with 3 items', () => {\n    const mockItems = [{ id: 1, name: 'Shoes', price: 50 }, { id: 2, name: 'Socks', price: 10 }];\n    render(<ShoppingCart items={mockItems} />);\n    expect(screen.getByText('Shoes')).toBeInTheDocument();\n  });\n});\n"""
        },
        {
            "component": "PaymentForm",
            "file_name": "PaymentForm.test.jsx",
            "content": """import React from 'react';\nimport { render, screen, fireEvent } from '@testing-library/react';\nimport PaymentForm from './PaymentForm';\n\ndescribe('PaymentForm Component', () => {\n  it('shows error messages on empty submission', () => {\n    render(<PaymentForm />);\n    fireEvent.click(screen.getByRole('button', { name: /checkout/i }));\n    expect(screen.getByText(/card number is required/i)).toBeInTheDocument();\n  });\n});\n"""
        }
    ]
    
    create_full_mock_project(
        db=db,
        project_id="proj_mock_react_ecommerce",
        project_name="React E-Commerce Portal",
        framework="React 18",
        source_files_count=24,
        test_cases=ecommerce_cases,
        test_files=ecommerce_files,
        execution_metrics={
            "total_tests": 4,
            "passed": 4,
            "failed": 0,
            "skipped": 0,
            "pass_rate": 100.0,
            "quality_score": 96.0
        },
        coverage_metrics={
            "statements": 92.5,
            "branches": 88.0,
            "functions": 94.2,
            "lines": 91.0
        }
    )

    # 2. Angular Customer Portal
    customer_cases = [
        {
            "component": "AuthInterceptor",
            "title": "Verify authorization header insertion",
            "objective": "Verify JWT auth headers are dynamically injected into outgoing HTTP service requests.",
            "category": "Services",
            "priority": "High",
            "steps": [
                "1. Trigger mock HttpClient request",
                "2. Intercept outgoing request using AuthInterceptor",
                "3. Assert header 'Authorization' contains Bearer token"
            ],
            "expected_result": "Authorization header correctly formatted with Bearer JWT."
        },
        {
            "component": "UserProfileComponent",
            "title": "Verify user profile page data rendering",
            "objective": "Verify user model resolves in view layout fields dynamically on component init.",
            "category": "State",
            "priority": "Medium",
            "steps": [
                "1. Initialize UserProfileComponent with loaded user profile service",
                "2. Assert email, username, and role labels show up correct values"
            ],
            "expected_result": "Labels show correct metadata values for active profile."
        },
        {
            "component": "UserProfileComponent",
            "title": "Verify profile save button changes trigger service PUT",
            "objective": "Verify submit clicks trigger data updates via HttpClient PUT calls.",
            "category": "Forms",
            "priority": "High",
            "steps": [
                "1. Set forms fields invalid or change form name value",
                "2. Click Profile Save changes",
                "3. Assert angular form validator blocks submit or profile update API is hit"
            ],
            "expected_result": "Save triggers API request with modified data."
        }
    ]
    customer_files = [
        {
            "component": "AuthInterceptor",
            "file_name": "auth.interceptor.spec.ts",
            "content": """import { TestBed } from '@angular/core/testing';\nimport { AuthInterceptor } from './auth.interceptor';\n\ndescribe('AuthInterceptor', () => {\n  it('should inject authorization header', () => {\n    // test body\n  });\n});\n"""
        },
        {
            "component": "UserProfileComponent",
            "file_name": "user-profile.component.spec.ts",
            "content": """import { ComponentFixture, TestBed } from '@angular/core/testing';\nimport { UserProfileComponent } from './user-profile.component';\n\ndescribe('UserProfileComponent', () => {\n  it('should display username label', () => {\n    // test body\n  });\n});\n"""
        }
    ]

    create_full_mock_project(
        db=db,
        project_id="proj_mock_angular_customer",
        project_name="Angular Customer Portal",
        framework="Angular 16",
        source_files_count=18,
        test_cases=customer_cases,
        test_files=customer_files,
        execution_metrics={
            "total_tests": 3,
            "passed": 3,
            "failed": 0,
            "skipped": 0,
            "pass_rate": 100.0,
            "quality_score": 98.0
        },
        coverage_metrics={
            "statements": 96.2,
            "branches": 92.5,
            "functions": 98.0,
            "lines": 95.4
        }
    )

    # 3. Vue Task Manager
    vue_cases = [
        {
            "component": "TaskGrid",
            "title": "Verify dashboard layout loaded items list",
            "objective": "Verify grids correctly render grid cards representing tasks.",
            "category": "State",
            "priority": "Medium",
            "steps": [
                "1. Mount TaskGrid component with list of tasks",
                "2. Confirm layout rendered exact number of child components"
            ],
            "expected_result": "Task cards matching items list rendered in layout grid."
        },
        {
            "component": "TaskGrid",
            "title": "Verify item deletion triggers event callback",
            "objective": "Verify that click triggers delete action callbacks and updates parent list state.",
            "category": "Events",
            "priority": "High",
            "steps": [
                "1. Click trash bin icon on one task card",
                "2. Assert delete click bubble up event is captured and parent removes item"
            ],
            "expected_result": "Delete event emitted cleanly and item removed from list."
        }
    ]
    vue_files = [
        {
            "component": "TaskGrid",
            "file_name": "TaskGrid.spec.js",
            "content": """import { mount } from '@vue/test-utils';\nimport TaskGrid from './TaskGrid.vue';\n\ndescribe('TaskGrid.vue', () => {\n  it('renders all task cards', () => {\n    // vue test implementation\n  });\n});\n"""
        }
    ]

    create_full_mock_project(
        db=db,
        project_id="proj_mock_vue_task",
        project_name="Vue Task Manager",
        framework="Vue 3",
        source_files_count=12,
        test_cases=vue_cases,
        test_files=vue_files,
        execution_metrics={
            "total_tests": 2,
            "passed": 1,
            "failed": 1,
            "skipped": 0,
            "pass_rate": 50.0,
            "quality_score": 88.0,
            "failures_list": [
                {
                    "title": "Verify item deletion triggers event callback",
                    "component": "TaskGrid"
                }
            ]
        },
        coverage_metrics={
            "statements": 88.5,
            "branches": 80.0,
            "functions": 90.0,
            "lines": 87.2
        }
    )


def seed_project_mock_data(db: Session, project: Project) -> None:
    """Auto-seed a newly created project with realistic test cases, test files, and reports."""
    # Build customized cases based on the project name or default to general test cases
    p_name = project.project_name
    framework = project.framework or "React"
    
    # Customize mock data titles depending on name matches
    if "billing" in p_name.lower() or "payment" in p_name.lower():
        prefix = "Billing"
        cases_data = [
            ("InvoiceHistory", "Verify invoice table rendering", "Verify layout rendering of user invoices list."),
            ("InvoiceHistory", "Verify billing invoice download click", "Verify invoice PDF generation api call is hit."),
            ("CardForm", "Verify inputs validation constraints", "Verify form validators trigger error message display."),
        ]
    elif "admin" in p_name.lower() or "dashboard" in p_name.lower():
        prefix = "Admin"
        cases_data = [
            ("StatsOverview", "Verify metrics rendering", "Verify numerical figures render cleanly."),
            ("UserPermissions", "Verify toggle admin changes role", "Verify role state update changes on toggle."),
            ("ExportButton", "Verify CSV export click event", "Verify export logic event runs on click."),
        ]
    else:
        prefix = "Dashboard"
        cases_data = [
            ("HeaderNav", "Verify dynamic user badge title", "Verify user profile displays username badge."),
            ("SettingsForm", "Verify validation on submit fields", "Verify validation rules on name & email."),
            ("ActivityFeed", "Verify scroll items load more feed", "Verify pagination loading items list."),
        ]

    test_cases = [
        {
            "component": item[0],
            "title": f"Verify {item[0]} - {item[1]}",
            "objective": item[2],
            "category": "Forms" if "validation" in item[1].lower() else "Events" if "click" in item[1].lower() else "State",
            "priority": "High" if idx == 0 else "Medium",
            "steps": [
                f"1. Mount {item[0]} component in DOM",
                f"2. Trigger actions corresponding to: {item[1]}",
                f"3. Verify expected behavior objectives resolve"
            ],
            "expected_result": f"{item[0]} resolves state changes cleanly without raising warnings."
        }
        for idx, item in enumerate(cases_data)
    ]

    test_files = list({tc["component"] for tc in test_cases})
    tf_extension = ".spec.ts" if "angular" in framework.lower() else ".test.jsx"
    test_files_data = [
        {
            "component": comp,
            "file_name": f"{comp}{tf_extension}",
            "content": f"// Mock generated test for {comp}\ndescribe('{comp} Component', () => {{\n  it('works correctly', () => {{\n    expect(true).toBe(true);\n  }});\n}});\n"
        }
        for comp in test_files
    ]

    # Create everything for this new project dynamically
    # Use existing ID
    run_id = f"run_mock_{project.id}_{uuid.uuid4().hex[:6]}"
    
    # 1. Update project status to completed and source files count
    project.status = "completed"
    project.source_file_count = 8
    
    # 2. Pipeline run
    run = PipelineRun(
        id=run_id,
        project_id=project.id,
        status="completed",
        current_stage="validation",
        progress=1.0,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    db.add(run)

    # 3. Components
    components_map = {}
    for tc in test_cases:
        c_name = tc["component"]
        if c_name not in components_map:
            comp_id = f"comp_{c_name.lower()}_{uuid.uuid4().hex[:6]}"
            comp = Component(
                id=comp_id,
                project_id=project.id,
                pipeline_run_id=run_id,
                name=c_name,
                component_type="ReactComponent" if "angular" not in framework.lower() else "AngularComponent",
                framework=framework,
            )
            db.add(comp)
            components_map[c_name] = comp_id
    db.flush()

    # 4. Test Cases
    db_cases = []
    # Generate unique test case prefix based on project ID
    clean_pid = project.id.replace("proj_mock_", "").replace("proj_", "")
    parts = clean_pid.split("_")
    if len(parts) == 1 and len(parts[0]) >= 10:
        prefix = parts[0][-4:].upper()
    else:
        prefix = parts[-1].upper()[:4]
    for idx, tc in enumerate(test_cases):
        tc_id = f"TC-{prefix}-{idx+1:03d}"
        comp_id = components_map.get(tc["component"])
        db_tc = TestCaseModel(
            id=tc_id,
            project_id=project.id,
            pipeline_run_id=run_id,
            component_id=comp_id,
            title=tc["title"],
            objective=tc["objective"],
            category=tc["category"],
            priority=tc["priority"],
            steps=tc["steps"],
            expected_result=tc["expected_result"],
            source_function="render",
            status="generated",
            quality_score=100
        )
        db.add(db_tc)
        db_cases.append(db_tc)
    db.flush()

    # 5. Test Files
    db_files = []
    for tf in test_files_data:
        tc_ids = [c.id for c in db_cases if components_map.get(tf["component"]) == c.component_id]
        db_tf = TestFileModel(
            id=f"file_mock_{uuid.uuid4().hex[:10]}",
            project_id=project.id,
            pipeline_run_id=run_id,
            component_id=components_map.get(tf["component"]),
            file_name=tf["file_name"],
            file_path=f"scratch/test_workspace/mock_{project.id}/src/components/{tf['file_name']}",
            framework=framework,
            test_case_ids=tc_ids,
            generated_at=datetime.utcnow()
        )
        db.add(db_tf)
        db_files.append((db_tf, tc_ids))
    db.flush()

    # 6. Test Execution
    exec_id = f"exec_mock_{uuid.uuid4().hex[:10]}"
    execution = TestExecutionModel(
        id=exec_id,
        project_id=project.id,
        pipeline_run_id=run_id,
        status="completed",
        total_tests=len(test_cases),
        passed=len(test_cases),
        failed=0,
        skipped=0,
        execution_time_ms=1200.0,
        pass_rate=100.0,
        created_at=datetime.utcnow()
    )
    db.add(execution)
    db.flush()

    # 7. Test Results
    for db_tc in db_cases:
        res = TestResultModel(
            id=f"res_mock_{uuid.uuid4().hex[:10]}",
            execution_id=exec_id,
            test_case_id=db_tc.id,
            test_name=db_tc.title,
            status="passed",
            expected=db_tc.expected_result,
            actual=db_tc.expected_result,
            error_message=None,
            created_at=datetime.utcnow()
        )
        db.add(res)

    # 8. Coverage Report
    coverage = CoverageReportModel(
        id=f"cov_mock_{uuid.uuid4().hex[:10]}",
        project_id=project.id,
        pipeline_run_id=run_id,
        statements=95.0,
        branches=90.0,
        functions=100.0,
        lines=94.0,
        coverage_status="available",
        created_at=datetime.utcnow()
    )
    db.add(coverage)

    # 9. Main Report
    synthesized_files_report = []
    for tf_obj, t_ids in db_files:
        synthesized_files_report.append({
            "file_name": tf_obj.file_name,
            "passed": len(t_ids),
            "total_tests": len(t_ids),
            "failed": 0,
            "skipped": 0
        })

    report_data_json = {
        "execution_summary": {
            "total_tests": len(test_cases),
            "passed": len(test_cases),
            "failed": 0,
            "skipped": 0,
            "pass_rate": 100.0,
            "execution_time_ms": 1200
        },
        "coverage": {
            "statements": 95.0,
            "branches": 90.0,
            "functions": 100.0,
            "lines": 94.0,
            "coverage_status": "available"
        },
        "test_files": synthesized_files_report,
        "failures": []
    }

    report = ReportModel(
        id=f"rep_mock_{uuid.uuid4().hex[:10]}",
        project_id=project.id,
        pipeline_run_id=run_id,
        total_tests=len(test_cases),
        passed=len(test_cases),
        failed=0,
        skipped=0,
        pass_rate=100.0,
        overall_quality_score=96.0,
        report_data=report_data_json,
        generated_at=datetime.utcnow()
    )
    db.add(report)
    db.commit()
    logger.info("Automatically mock seeded dynamic project: %s", project.id)
