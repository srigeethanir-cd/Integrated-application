import json
import tempfile
from pathlib import Path

from agents.agent1_blueprint.agent1 import Agent1Blueprint


def test_agent1_generates_manifest_blueprint_and_plan():
    agent = Agent1Blueprint()
    stories = [
        {
            "id": "US-1",
            "title": "User can sign up",
            "description": "As a user, I want to sign up so that I can access the portal.",
            "acceptance_criteria": ["User can create account", "User receives confirmation email"],
        },
        {
            "id": "US-2",
            "title": "Admin can manage projects",
            "description": "As an admin, I want to manage projects so that I can supervise work.",
            "acceptance_criteria": ["Admin can create projects", "Admin can archive projects"],
        },
    ]
    tech_stack = "Python FastAPI React PostgreSQL Docker"

    result = agent.process(stories, tech_stack, output_dir=tempfile.mkdtemp())

    assert result["status"] == "awaiting_human_approval"
    assert result["project_manifest"]["project_name"]
    assert result["master_blueprint"]["modules"]
    assert result["implementation_plan"]["phases"]
    assert "text_plan" in result["implementation_plan"]
    assert "Foundation" in result["implementation_plan"]["text_plan"]
    assert result["shared_components"]
    assert "ui_text" in result
    assert "Blueprint" in result["ui_text"]
    assert "Implementation Plan" in result["ui_text"]


def test_agent1_can_approve_and_prepare_agent2():
    agent = Agent1Blueprint()
    stories = [{"id": "US-1", "title": "User can authenticate", "description": "As a user, I want to authenticate"}]

    result = agent.process(stories, "Python FastAPI PostgreSQL", output_dir=tempfile.mkdtemp())
    approved = agent.handle_human_decision(result, "approved")

    assert approved["status"] == "ready_for_agent2"
    assert approved["agent2_ready"] is True


def test_agent1_can_regenerate_from_feedback():
    agent = Agent1Blueprint()
    stories = [{"id": "US-1", "title": "User can authenticate", "description": "As a user, I want to authenticate"}]

    result = agent.process(stories, "Python FastAPI PostgreSQL", output_dir=tempfile.mkdtemp())
    regenerated = agent.handle_human_decision(result, "regenerate", feedback="Prioritize mobile-first UX")

    assert regenerated["status"] == "regenerated"
    assert regenerated["master_blueprint"]["summary"].lower().find("mobile") >= 0


def test_agent1_comprehensive_workflow():
    agent = Agent1Blueprint()
    stories = [
        {
            "id": "US-1",
            "title": "User login",
            "description": "As a user, I want to log in with username and password.",
            "feature_group": "authentication"
        }
    ]
    tech_stack = "Python FastAPI React PostgreSQL Docker"
    out_dir = tempfile.mkdtemp()
    result = agent.process(stories, tech_stack, output_dir=out_dir)

    # 1. Check all 8 blueprints are created in output JSONs
    assert result["status"] == "awaiting_human_approval"
    artifacts = result["artifacts"]
    assert "project_manifest" in artifacts
    assert "master_blueprint" in artifacts
    assert "implementation_plan" in artifacts
    assert "shared_components" in artifacts
    assert "folder_structure_blueprint" in artifacts
    assert "api_contracts" in artifacts
    assert "database_blueprint" in artifacts
    assert "dependency_blueprint" in artifacts
    assert "review_report" in artifacts

    # Check on disk existence of all 8 JSONs and 1 MD
    for k, filepath in artifacts.items():
        assert Path(filepath).exists()

    # 2. Check human readable report contains the required disclaimer message at the end
    report_content = Path(artifacts["review_report"]).read_text(encoding="utf-8")
    assert "Approving this blueprint will create the project skeleton and hand over the project to Agent-2." in report_content
    assert "Project Summary" in report_content
    assert "Technology Stack" in report_content
    assert "Modules" in report_content
    assert "Shared Components" in report_content
    assert "Project Folder Structure" in report_content
    assert "Database Summary" in report_content
    assert "API Summary" in report_content

    # 3. Prior to approval, folders are NOT created
    project_manifest = result["project_manifest"]
    project_name = project_manifest.get("project_name", "generated_project")
    import re
    safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", project_name).strip("_").lower()
    project_path = Path(out_dir) / "projects" / safe_name
    assert not project_path.exists()

    # 4. Perform approval
    proj_dir = tempfile.mkdtemp()
    approved = agent.handle_human_decision(result, "approved", output_dir=proj_dir)

    # 5. Check approved result matches the strict Agent-2 handoff format
    assert approved["status"] == "ready_for_agent2"
    assert approved["agent2_ready"] is True
    assert "folder_structure_blueprint" in approved
    assert "api_contracts" in approved
    assert "database_blueprint" in approved
    assert "dependency_blueprint" in approved
    assert "metadata" in approved
    assert "workspace_path" in approved
    # Report should NOT be in the approved handoff dictionary
    assert "review_report" not in approved
    assert "review_report_content" not in approved

    # 6. Verify post approval folder skeleton is created on disk
    approved_proj_path = Path(proj_dir) / safe_name
    assert approved_proj_path.exists()
    assert (approved_proj_path / "backend").exists()
    assert (approved_proj_path / "frontend").exists()
    assert (approved_proj_path / "shared").exists()
    assert (approved_proj_path / "workspace").exists()
    assert (approved_proj_path / "metadata").exists()

    # Blueprints should be saved in approved_proj_path / "metadata"
    assert (approved_proj_path / "metadata" / "ProjectManifest.json").exists()
    assert (approved_proj_path / "metadata" / "MasterBlueprint.json").exists()
    assert (approved_proj_path / "metadata" / "FolderStructureBlueprint.json").exists()

