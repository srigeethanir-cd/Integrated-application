"""Top-level FastAPI REST API router registration for AI BA Accelerator."""

from fastapi import APIRouter

# Core & Feature Routes
from app.api.v1.authentication import router as authentication_router
from app.api.v1.project_routes import router as project_router
from app.api.v1.document_routes import router as document_router
from app.api.v1.agent_execution_routes import router as agent_execution_router
from app.api.v1.agent2_routes import router as agent2_router
from app.api.v1.workspace_routes import router as workspace_router
from app.api.v1.regeneration_routes import router as regeneration_router
from app.api.v1.reporting_routes import router as reporting_router
from app.api.v1.deployment_routes import router as deployment_router
from app.api.v1.end_to_end_workflow import router as end_to_end_workflow_router
from app.api.v1.code_gene_routes import router as code_gene_router
from app.api.v1.blueprint_routes import router as blueprint_router
from app.api.v1.epic_routes import router as epic_router
from app.api.v1.story_routes import router as story_router
from app.api.v1.component_routes import router as component_router
from app.api.v1.file_routes import router as file_router
from app.api.v1.prompt_template_routes import router as prompt_template_router
from app.api.v1.integrated_project_routes import router as integrated_project_router
from app.api.v1.request_change_routes import router as request_change_router

# Sub-system Routes
from app.approval.approval_router import router as approval_router
from langgraph.router import router as workflow_router
from traceability.router import router as traceability_router
from validators.router import router as validators_router

# Master Router (included by main.py under prefix=settings.api_prefix which is /api/v1)
api_router = APIRouter()

api_router.include_router(end_to_end_workflow_router)
api_router.include_router(code_gene_router, prefix="/code-gene", tags=["Code-Gene"])
api_router.include_router(authentication_router)
api_router.include_router(project_router)
api_router.include_router(document_router)
api_router.include_router(agent_execution_router)
api_router.include_router(agent2_router)
api_router.include_router(workspace_router)
api_router.include_router(regeneration_router)
api_router.include_router(reporting_router)
api_router.include_router(deployment_router)
api_router.include_router(integrated_project_router)
api_router.include_router(approval_router)
api_router.include_router(workflow_router)
api_router.include_router(traceability_router)
api_router.include_router(validators_router)
api_router.include_router(blueprint_router)
api_router.include_router(epic_router)
api_router.include_router(story_router)
api_router.include_router(component_router)
api_router.include_router(file_router)
api_router.include_router(prompt_template_router)
api_router.include_router(request_change_router)

