from fastapi import APIRouter, HTTPException
from mistralai.client import Mistral
from mistralai.client.models import WorkflowExecutionResponse

from src.core.config import settings
from src.schemas.company import CompanyRequest, StatusResponse, TriggerResponse

router = APIRouter(prefix="/company", tags=["workflows"])

_client = Mistral(api_key=settings.MISTRAL_API_KEY)


@router.post("", response_model=TriggerResponse)
def trigger_workflow(body: CompanyRequest) -> TriggerResponse:
    execution = _client.workflows.execute_workflow(
        workflow_identifier=settings.DEPLOYMENT_NAME,
        input={"company_name": body.company_name},
    )
    if isinstance(execution, WorkflowExecutionResponse):
        status = str(execution.status or "RUNNING")
    else:
        status = "COMPLETED"
    return TriggerResponse(execution_id=execution.execution_id, status=status)


@router.get("/{execution_id}", response_model=StatusResponse)
def get_execution_status(execution_id: str) -> StatusResponse:
    execution = _client.workflows.executions.get_workflow_execution(
        execution_id=execution_id,
    )
    if execution.status is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return StatusResponse(
        execution_id=execution.execution_id,
        status=str(execution.status),
        result=execution.result,
    )
