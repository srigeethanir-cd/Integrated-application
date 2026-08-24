import os
import json
import uuid
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.core.config import get_settings
from ui_visualization.folder_tree_visualizer import FolderTreeVisualizer
from ui_visualization.component_visualizer import ComponentVisualizer
from ui_visualization.dependency_visualizer import DependencyVisualizer
from ui_visualization.api_visualizer import ApiVisualizer
from ui_visualization.database_visualizer import DatabaseVisualizer
from ui_visualization.preview_generator import PreviewGenerator
from ui_visualization.approval_service import ApprovalService

settings = get_settings()

def test_folder_tree_visualizer(tmp_path):
    """Test FolderTreeVisualizer recursive tree generation."""
    # Setup folders
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file1.txt").write_text("hello")
    (tmp_path / "subdir" / "file2.txt").write_text("world")

    viz = FolderTreeVisualizer()
    tree = viz.generate_tree(tmp_path)
    
    assert tree["name"] == tmp_path.name
    assert tree["type"] == "directory"
    assert len(tree["children"]) == 2


def test_component_visualizer(tmp_path):
    """Test ComponentVisualizer parsing React components."""
    (tmp_path / "Comp.tsx").write_text("""
import React from 'react';
import Child from './Child';
interface CompProps {
    title: string;
}
export default function Comp(props: CompProps) {
    return <div>{props.title}</div>;
}
""")
    viz = ComponentVisualizer()
    res = viz.scan_components(tmp_path)
    
    assert res["type"] == "hierarchy"
    assert len(res["children"]) == 1
    assert res["children"][0]["name"] == "Comp"
    assert res["children"][0]["props"] == "CompProps"


def test_dependency_visualizer(tmp_path):
    """Test DependencyVisualizer scanner."""
    (tmp_path / "a.py").write_text("import os\nfrom app.core import config")
    viz = DependencyVisualizer()
    graph = viz.generate_graph(tmp_path)
    
    assert "nodes" in graph
    assert "links" in graph
    assert len(graph["nodes"]) == 1


def test_api_visualizer(tmp_path):
    """Test ApiVisualizer scanner."""
    (tmp_path / "story_router.py").write_text("""
@router.get('/api/v1/test')
def test_route():
    return {}
""")
    viz = ApiVisualizer()
    graph = viz.generate_api_graph(tmp_path)
    
    assert graph["total_endpoints"] == 1
    assert graph["endpoints"][0]["method"] == "GET"
    assert graph["endpoints"][0]["path"] == "/api/v1/test"


def test_database_visualizer(tmp_path):
    """Test DatabaseVisualizer schema parser."""
    (tmp_path / "schema.sql").write_text("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255)
);
""")
    viz = DatabaseVisualizer()
    er = viz.generate_er_diagram(tmp_path)
    
    assert len(er["tables"]) == 1
    assert er["tables"][0]["table_name"] == "users"


def test_approval_service_error_recovery():
    """Test ApprovalService's root cause analysis and recovery routing."""
    service = ApprovalService()
    
    # UI mismatch detection
    ui_res = service.analyze_rejection_root_cause("UI layout is slightly off", [])
    assert ui_res["responsible_agent"] == "Agent0"
    
    # Blueprint issue detection
    bp_res = service.analyze_rejection_root_cause("Contract spec is missing the route mapping", [])
    assert bp_res["responsible_agent"] == "Agent1"
    
    # Naming standards / validation checks
    val_res = service.analyze_rejection_root_cause("naming standards check failed", [])
    assert val_res["responsible_agent"] == "Validation Engine"
    
    # Default to Agent 2
    def_res = service.analyze_rejection_root_cause("Backend logic is failing with 500 error", [])
    assert def_res["responsible_agent"] == "Agent2"
