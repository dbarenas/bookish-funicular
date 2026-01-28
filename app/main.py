from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query

from .models import (
    AuditLogResponse,
    CaseFormData,
    CaseReportAggregates,
    CaseReportNarrative,
    CaseReportResponse,
    CaseStatusResponse,
    ClinicalContext,
    ClinicalDecisionData,
    DeleteResponse,
    ErrorResponse,
    GetSectionResponse,
    IngestCaseResponse,
    LockResponse,
    PatientsContext,
    ReportSectionStatus,
    SectionName,
    SubmitCaseRequest,
    SubmitCaseResponse,
    TraceResponse,
    TreatmentGoalsData,
)
from .storage import CaseRepository

app = FastAPI(title="CUSE Case API")
repo = CaseRepository()


@app.post("/cases", response_model=IngestCaseResponse, responses={400: {"model": ErrorResponse}})
def create_case(payload: CaseFormData) -> IngestCaseResponse:
    record = repo.create_case(payload, owner_user_id="user-123")
    return IngestCaseResponse(case_id=record.case_id, data=record.data)


@app.put("/cases/{case_id}", response_model=IngestCaseResponse, responses={404: {"model": ErrorResponse}})
def upsert_case(case_id: str, payload: CaseFormData) -> IngestCaseResponse:
    record = repo.upsert_case(case_id, payload, actor="user-123")
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    return IngestCaseResponse(case_id=record.case_id, data=record.data)


@app.patch(
    "/cases/{case_id}/patients-context",
    response_model=IngestCaseResponse,
    responses={404: {"model": ErrorResponse}},
)
def patch_patients_context(case_id: str, payload: PatientsContext) -> IngestCaseResponse:
    record = repo.update_section(case_id, SectionName.patientsContext, payload, actor="user-123")
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    return IngestCaseResponse(case_id=record.case_id, data=record.data)


@app.patch(
    "/cases/{case_id}/clinical-context",
    response_model=IngestCaseResponse,
    responses={404: {"model": ErrorResponse}},
)
def patch_clinical_context(case_id: str, payload: ClinicalContext) -> IngestCaseResponse:
    record = repo.update_section(case_id, SectionName.clinicalContext, payload, actor="user-123")
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    return IngestCaseResponse(case_id=record.case_id, data=record.data)


@app.patch(
    "/cases/{case_id}/treatment-goals",
    response_model=IngestCaseResponse,
    responses={404: {"model": ErrorResponse}},
)
def patch_treatment_goals(case_id: str, payload: TreatmentGoalsData) -> IngestCaseResponse:
    record = repo.update_section(case_id, SectionName.treatmentGoals, payload, actor="user-123")
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    return IngestCaseResponse(case_id=record.case_id, data=record.data)


@app.patch(
    "/cases/{case_id}/clinical-decision",
    response_model=IngestCaseResponse,
    responses={404: {"model": ErrorResponse}},
)
def patch_clinical_decision(case_id: str, payload: ClinicalDecisionData) -> IngestCaseResponse:
    record = repo.update_section(case_id, SectionName.clinicalDecision, payload, actor="engine")
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    return IngestCaseResponse(case_id=record.case_id, data=record.data)


@app.get("/cases/{case_id}", response_model=CaseFormData, responses={404: {"model": ErrorResponse}})
def get_case(case_id: str) -> CaseFormData:
    record = repo.get_case(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    return record.data


@app.get(
    "/cases/{case_id}/section/{section_name}",
    response_model=GetSectionResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_case_section(case_id: str, section_name: SectionName) -> GetSectionResponse:
    record = repo.get_case(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    data = getattr(record.data, section_name.value)
    return GetSectionResponse(case_id=record.case_id, section=section_name, data=data)


@app.get(
    "/cases/{case_id}/status",
    response_model=CaseStatusResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_case_status(case_id: str) -> CaseStatusResponse:
    record = repo.get_case(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    completed: List[SectionName] = []
    missing_required: List[str] = []
    for section in SectionName:
        if getattr(record.data, section.value) is not None:
            completed.append(section)
        else:
            missing_required.append(section.value)
    current_step = completed[-1] if completed else None
    return CaseStatusResponse(
        case_id=record.case_id,
        current_step=current_step,
        completed_steps=completed,
        missing_required=missing_required,
        locked=record.locked,
        updated_at=record.updated_at,
    )


@app.post(
    "/cases/{case_id}/submit",
    response_model=SubmitCaseResponse,
    responses={404: {"model": ErrorResponse}},
)
def submit_case(case_id: str, payload: SubmitCaseRequest) -> SubmitCaseResponse:
    record = repo.get_case(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    missing_required = [section.value for section in SectionName if getattr(record.data, section.value) is None]
    success = not missing_required
    locked = record.locked
    if success and not payload.validate_only:
        record = repo.set_lock(case_id, True, actor="system")
        locked = True if record else locked
    return SubmitCaseResponse(
        success=success,
        case_id=case_id,
        missing_required=missing_required,
        locked=locked,
    )


@app.get(
    "/cases/{case_id}/report",
    response_model=CaseReportResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_case_report(
    case_id: str,
    include_trace: bool = Query(False),
    include_audit: bool = Query(False),
    include_raw: bool = Query(False),
    format: Optional[str] = Query(None),
) -> CaseReportResponse:
    record = repo.get_case(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    sections_status = {
        section: ReportSectionStatus(completed=getattr(record.data, section.value) is not None)
        for section in SectionName
    }
    patient_overview = "Paciente sin datos." if not record.data.patientsContext else "Paciente con datos cargados."
    clinical_overview = "Sin contexto clínico." if not record.data.clinicalContext else "Contexto clínico disponible."
    narrative = CaseReportNarrative(
        patient_overview=patient_overview,
        clinical_overview=clinical_overview,
        treatment_goals_overview="Metas definidas." if record.data.treatmentGoals else None,
        decision_overview="Decisión clínica calculada." if record.data.clinicalDecision else None,
    )
    aggregates = CaseReportAggregates(
        age=record.data.patientsContext.age if record.data.patientsContext else None,
        gender=record.data.patientsContext.gender if record.data.patientsContext else None,
        performance_status=record.data.patientsContext.performance_status if record.data.patientsContext else None,
        comorbidities=[item.condition for item in record.data.patientsContext.comorbidities]
        if record.data.patientsContext and record.data.patientsContext.comorbidities
        else [],
        bclc_stage=record.data.clinicalContext.barcelona_stage if record.data.clinicalContext else None,
        child_pugh=record.data.clinicalContext.child_pugh_score if record.data.clinicalContext else None,
        meld=record.data.clinicalContext.meld_score if record.data.clinicalContext else None,
        top_goals=[goal.label for goal in record.data.treatmentGoals.selectedGoals if goal.priority.value == "top"]
        if record.data.treatmentGoals
        else [],
        mid_goals=[goal.label for goal in record.data.treatmentGoals.selectedGoals if goal.priority.value == "mid"]
        if record.data.treatmentGoals
        else [],
        low_goals=[goal.label for goal in record.data.treatmentGoals.selectedGoals if goal.priority.value == "low"]
        if record.data.treatmentGoals
        else [],
        fto=record.data.clinicalDecision.fto if record.data.clinicalDecision else None,
        final_id=record.data.clinicalDecision.finalId if record.data.clinicalDecision else None,
        stage_label=record.data.clinicalDecision.stageLabel if record.data.clinicalDecision else None,
        result_label=record.data.clinicalDecision.resultLabel if record.data.clinicalDecision else None,
    )
    response = CaseReportResponse(
        case_id=record.case_id,
        sections_status=sections_status,
        narrative=narrative,
        aggregates=aggregates,
        decision_path=record.data.clinicalDecision.path if record.data.clinicalDecision else None,
    )
    if include_trace:
        response.trace = TraceResponse(
            case_id=record.case_id,
            owner_user_id=record.owner_user_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
            schema_version=record.schema_version,
            engine_version=record.engine_version,
            prompt_version=record.prompt_version,
            correlation_id=record.correlation_id,
            session_id=record.session_id,
        )
    if include_audit:
        response.audit_log = record.audit_log
    if include_raw:
        response.raw = record.data
    _ = format
    return response


@app.get(
    "/cases/{case_id}/audit-log",
    response_model=AuditLogResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_case_audit_log(case_id: str) -> AuditLogResponse:
    record = repo.get_case(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    return AuditLogResponse(case_id=record.case_id, events=record.audit_log)


@app.get(
    "/cases/{case_id}/trace",
    response_model=TraceResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_case_trace(case_id: str) -> TraceResponse:
    record = repo.get_case(case_id)
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    return TraceResponse(
        case_id=record.case_id,
        owner_user_id=record.owner_user_id,
        created_at=record.created_at,
        updated_at=record.updated_at,
        schema_version=record.schema_version,
        engine_version=record.engine_version,
        prompt_version=record.prompt_version,
        correlation_id=record.correlation_id,
        session_id=record.session_id,
    )


@app.post(
    "/cases/{case_id}/lock",
    response_model=LockResponse,
    responses={404: {"model": ErrorResponse}},
)
def lock_case(case_id: str) -> LockResponse:
    record = repo.set_lock(case_id, True, actor="system")
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    return LockResponse(case_id=record.case_id, locked=record.locked, updated_at=record.updated_at)


@app.post(
    "/cases/{case_id}/unlock",
    response_model=LockResponse,
    responses={404: {"model": ErrorResponse}},
)
def unlock_case(case_id: str) -> LockResponse:
    record = repo.set_lock(case_id, False, actor="admin")
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    return LockResponse(case_id=record.case_id, locked=record.locked, updated_at=record.updated_at)


@app.delete(
    "/cases/{case_id}",
    response_model=DeleteResponse,
    responses={404: {"model": ErrorResponse}},
)
def delete_case(case_id: str) -> DeleteResponse:
    record = repo.delete_case(case_id, actor="admin")
    if not record:
        raise HTTPException(status_code=404, detail="case_not_found")
    return DeleteResponse(case_id=record.case_id)
