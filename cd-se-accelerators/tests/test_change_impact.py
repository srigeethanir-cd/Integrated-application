import pytest
from datetime import datetime, timedelta
from app.models.ir_models import (
    FrameworkAgnosticIR, 
    ComponentIR, 
    ServiceDependency, 
    RouteModel, 
    ComponentRelationshipInfo, 
    DependencyNode
)
from app.models.test_case_models import TestCase
from app.db.models import ProjectSnapshot, FileSnapshot, Project, PipelineRun
from app.services.change_impact.dependency_analyzer import DependencyAnalyzer
from app.services.change_impact.impact_analyzer import ImpactAnalyzer
from app.services.change_impact.test_selection_service import TestSelectionService
from app.services.change_impact.snapshot_service import SnapshotService
from app.services.change_impact.file_diff_service import FileDiffService


@pytest.fixture
def mock_ir():
    """Create a sample mock framework-agnostic IR for testing."""
    return FrameworkAgnosticIR(
        project_name="DemoApp",
        framework="React",
        components=[
            ComponentIR(
                name="LoginForm",
                file_path="src/components/LoginForm/LoginForm.jsx",
                source_file="src/components/LoginForm/LoginForm.jsx",
                type="functional"
            ),
            ComponentIR(
                name="Dashboard",
                file_path="src/components/Dashboard/Dashboard.jsx",
                source_file="src/components/Dashboard/Dashboard.jsx",
                type="functional"
            ),
            ComponentIR(
                name="App",
                file_path="src/App.jsx",
                source_file="src/App.jsx",
                type="functional"
            )
        ],
        services=[
            ServiceDependency(name="authService", type="service_call")
        ],
        routes=[
            RouteModel(path="/login", component="LoginForm")
        ],
        component_relationships=[
            ComponentRelationshipInfo(component="LoginForm", parent="App", children=[], depth=1),
            ComponentRelationshipInfo(component="Dashboard", parent="App", children=[], depth=1)
        ],
        dependency_graph=[
            DependencyNode(
                component="LoginForm",
                imports_components=[],
                imports_services=["authService"]
            ),
            DependencyNode(
                component="App",
                imports_components=["LoginForm", "Dashboard"]
            )
        ]
    )


@pytest.fixture
def mock_test_cases():
    """Create a list of mock test cases mapping to components."""
    return [
        TestCase(
            id="TC-LoginForm-001",
            strategy_id="STRAT-1",
            edge_case_id="EC-1",
            category="Forms",
            priority="High",
            component="LoginForm",
            title="Submit login form successfully",
            objective="Verify form inputs submit successfully",
            expected_result="User is logged in",
            metadata={
                "component": "LoginForm",
                "element": "form",
                "element_type": "form",
                "locator": {"strategy": "role", "value": "form"},
                "action": "submit",
                "assertion_type": "exists",
                "assertion_target": "Dashboard"
            }
        ),
        TestCase(
            id="TC-Dashboard-001",
            strategy_id="STRAT-2",
            edge_case_id="EC-2",
            category="General",
            priority="Medium",
            component="Dashboard",
            title="Render dashboard cleanly",
            objective="Verify main view renders",
            expected_result="Dashboard visible",
            metadata={
                "component": "Dashboard",
                "element": "h1",
                "element_type": "heading",
                "locator": {"strategy": "role", "value": "heading"},
                "action": "render",
                "assertion_type": "exists",
                "assertion_target": "Welcome"
            }
        ),
        TestCase(
            id="TC-App-001",
            strategy_id="STRAT-3",
            edge_case_id="EC-3",
            category="Routing",
            priority="Medium",
            component="App",
            title="Navigate to login page",
            objective="Verify initial routing",
            expected_result="LoginForm mounted",
            metadata={
                "component": "App",
                "element": "router",
                "element_type": "router",
                "locator": {"strategy": "url", "value": "/login"},
                "action": "navigate",
                "assertion_type": "exists",
                "assertion_target": "LoginForm"
            }
        )
    ]


@pytest.fixture
def mock_manifest():
    """Create a mock test manifest matching test cases."""
    return {
        "pipeline_run_id": "run_test_123",
        "generated_files": [
            {
                "component": "LoginForm",
                "file_name": "LoginForm.test.jsx",
                "file_path": "tests/react/LoginForm.test.jsx",
                "test_cases": ["TC-LoginForm-001"]
            },
            {
                "component": "Dashboard",
                "file_name": "Dashboard.test.jsx",
                "file_path": "tests/react/Dashboard.test.jsx",
                "test_cases": ["TC-Dashboard-001"]
            },
            {
                "component": "App",
                "file_name": "App.test.jsx",
                "file_path": "tests/react/App.test.jsx",
                "test_cases": ["TC-App-001"]
            }
        ]
    }


def test_dependency_analyzer(mock_ir):
    analyzer = DependencyAnalyzer(mock_ir)
    
    # Verify lookup by name
    assert "LoginForm" in analyzer.components_by_name
    assert "Dashboard" in analyzer.components_by_name
    
    # Verify lookup by file
    comp = analyzer.get_component_by_file("src/components/LoginForm/LoginForm.jsx")
    assert comp is not None
    assert comp.name == "LoginForm"

    # Verify parent retrieval
    parents = analyzer.get_parent_components("LoginForm")
    assert "App" in parents


def test_impact_analyzer_direct_change(mock_ir):
    dep_analyzer = DependencyAnalyzer(mock_ir)
    impact_analyzer = ImpactAnalyzer(dep_analyzer)
    
    changed_files = ["src/components/LoginForm/LoginForm.jsx"]
    impacted, reasons, _ = impact_analyzer.analyze_changed_files(changed_files)
    
    # Direct modified is HIGH impact
    assert impacted.get("LoginForm") == "HIGH"
    # Parent (App) importing LoginForm becomes MEDIUM impact
    assert impacted.get("App") == "MEDIUM"
    # Dashboard is unaffected by LoginForm modifications
    assert "Dashboard" not in impacted


def test_impact_analyzer_service_change(mock_ir):
    dep_analyzer = DependencyAnalyzer(mock_ir)
    impact_analyzer = ImpactAnalyzer(dep_analyzer)
    
    changed_files = ["src/services/authService.js"]
    impacted, _, _ = impact_analyzer.analyze_changed_files(changed_files)
    
    # LoginForm imports authService, so it should be impacted (HIGH/MEDIUM)
    assert "LoginForm" in impacted
    # App imports LoginForm, so it should be impacted (MEDIUM)
    assert "App" in impacted


def test_impact_analyzer_unknown_file(mock_ir):
    dep_analyzer = DependencyAnalyzer(mock_ir)
    impact_analyzer = ImpactAnalyzer(dep_analyzer)
    
    changed_files = ["package.json"]
    impacted, _, global_reasons = impact_analyzer.analyze_changed_files(changed_files)
    
    # Global changes select all tests with LOW priority to prevent incorrect exclusion
    assert len(global_reasons) > 0
    assert impacted.get("LoginForm") == "LOW"
    assert impacted.get("Dashboard") == "LOW"
    assert impacted.get("App") == "LOW"


def test_test_selection_service(mock_ir, mock_test_cases, mock_manifest):
    dep_analyzer = DependencyAnalyzer(mock_ir)
    impact_analyzer = ImpactAnalyzer(dep_analyzer)
    selection_service = TestSelectionService()
    
    changed_files = ["src/components/LoginForm/LoginForm.jsx"]
    impacted, reasons, global_reasons = impact_analyzer.analyze_changed_files(changed_files)
    
    response = selection_service.select_tests(
        test_cases=mock_test_cases,
        manifest=mock_manifest,
        impacted_components=impacted,
        impact_reasons=reasons,
        global_reasons=global_reasons,
        changed_files=changed_files
    )
    
    assert response.total_tests == 3
    assert response.impacted_tests == 2  # LoginForm (HIGH) + App (MEDIUM)
    assert response.unaffected_tests == 1  # Dashboard (unaffected)
    assert response.estimated_reduction_percent == 33.3
    
    # Check traceability step contains test case ids
    recommended_ids = {t.test_case_id for t in response.recommended_tests}
    assert "TC-LoginForm-001" in recommended_ids
    assert "TC-App-001" in recommended_ids
    assert "TC-Dashboard-001" not in recommended_ids


def test_snapshot_diffing_added_modified_deleted():
    """Verify file diff detection based on project snapshots and content hashes."""
    diff_service = FileDiffService()
    
    # Create two mock project snapshots
    prev_snap = ProjectSnapshot(id="snap_1", project_id="proj_1", pipeline_run_id="run_1", workspace_path="path_1")
    prev_snap.file_snapshots = [
        FileSnapshot(file_path="src/components/LoginForm.jsx", content_hash="hash_a", file_size=100),
        FileSnapshot(file_path="src/components/Dashboard.jsx", content_hash="hash_b", file_size=200),
        FileSnapshot(file_path="src/utils/math.js", content_hash="hash_c", file_size=50),
    ]

    curr_snap = ProjectSnapshot(id="snap_2", project_id="proj_1", pipeline_run_id="run_2", workspace_path="path_1")
    curr_snap.file_snapshots = [
        FileSnapshot(file_path="src/components/LoginForm.jsx", content_hash="hash_a_modified", file_size=120),  # modified
        # Dashboard.jsx is deleted
        FileSnapshot(file_path="src/utils/math.js", content_hash="hash_c", file_size=50),  # unchanged
        FileSnapshot(file_path="src/components/Sidebar.jsx", content_hash="hash_d", file_size=150),  # added
    ]

    diff = diff_service.diff_snapshots(prev_snap, curr_snap)
    
    assert diff["modified_files"] == ["src/components/LoginForm.jsx"]
    assert diff["added_files"] == ["src/components/Sidebar.jsx"]
    assert diff["deleted_files"] == ["src/components/Dashboard.jsx"]
    assert diff["unchanged_files"] == ["src/utils/math.js"]


def test_snapshot_timestamp_ignored():
    """Verify that timestamp updates do not flag file modification if content hash remains identical."""
    diff_service = FileDiffService()
    
    # Same content hash, different modification time
    prev_snap = ProjectSnapshot(id="snap_1", project_id="proj_1", pipeline_run_id="run_1", workspace_path="path_1")
    prev_snap.file_snapshots = [
        FileSnapshot(file_path="src/components/LoginForm.jsx", content_hash="hash_abc", file_size=100, modified_at=datetime.utcnow() - timedelta(hours=1))
    ]

    curr_snap = ProjectSnapshot(id="snap_2", project_id="proj_1", pipeline_run_id="run_2", workspace_path="path_1")
    curr_snap.file_snapshots = [
        FileSnapshot(file_path="src/components/LoginForm.jsx", content_hash="hash_abc", file_size=100, modified_at=datetime.utcnow())
    ]

    diff = diff_service.diff_snapshots(prev_snap, curr_snap)
    
    assert len(diff["modified_files"]) == 0
    assert diff["unchanged_files"] == ["src/components/LoginForm.jsx"]
