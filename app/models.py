from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Priority(str, Enum):
    top = "top"
    mid = "mid"
    low = "low"
    equal = "equal"


class Comorbidity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    condition: str = Field(..., description="ID de la condición (ej: diabetes_type_2, hypertension).")
    severity: Optional[Literal["mild", "moderate", "severe"]] = Field(default=None)
    controlled: Optional[bool] = Field(default=None)
    medications: Optional[List[str]] = Field(default=None)


class PreviousTreatment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    treatment_type: str
    agent: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    response: Optional[str] = None


class PatientsContext(BaseModel):
    """
    Objeto flexible: tipa campos comunes y permite extra keys.
    """

    model_config = ConfigDict(extra="allow")

    age: Optional[int] = Field(default=None, ge=0, le=130)
    gender: Optional[str] = None
    weight: Optional[float] = Field(default=None, ge=0, description="Kg")
    height: Optional[float] = Field(default=None, ge=0, description="Cm")
    ethnicity: Optional[str] = None

    performance_status: Optional[str] = None
    smoking_history: Optional[str] = None
    alcohol_consumption: Optional[str] = None

    family_history_hcc: Optional[bool] = None
    family_history_cirrhosis: Optional[bool] = None

    comorbidities: Optional[List[Comorbidity]] = None
    previous_treatments: Optional[List[PreviousTreatment]] = None

    allergies: Optional[str] = None
    insurance_coverage: Optional[str] = None
    geographic_location: Optional[str] = None


class ImagingFinding(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    date: Optional[date] = None
    findings: Optional[str] = None
    contrast_enhancement: Optional[str] = None
    radiologist_assessment: Optional[str] = None
    liver_surface: Optional[str] = None


class Histology(BaseModel):
    model_config = ConfigDict(extra="allow")

    tumor_grade: Optional[str] = None
    histological_type: Optional[str] = None
    fibrosis_stage: Optional[str] = None
    inflammation_grade: Optional[str] = None


class ClinicalContext(BaseModel):
    """
    Objeto flexible: tipa campos comunes y permite extra keys.
    """

    model_config = ConfigDict(extra="allow")

    tumor_location: Optional[str] = None
    tumor_size: Optional[float] = Field(default=None, ge=0, description="cm")
    number_of_lesions: Optional[int] = Field(default=None, ge=0)
    largest_lesion_size: Optional[float] = Field(default=None, ge=0, description="cm")
    tumor_distribution: Optional[str] = None
    vascular_invasion: Optional[bool] = None
    extrahepatic_spread: Optional[bool] = None

    barcelona_stage: Optional[str] = None
    child_pugh_score: Optional[str] = None
    child_pugh_points: Optional[int] = Field(default=None, ge=0)
    meld_score: Optional[int] = Field(default=None, ge=0)
    milan_criteria: Optional[bool] = None

    portal_hypertension: Optional[bool] = None
    ascites: Optional[str] = None
    encephalopathy: Optional[bool] = None
    varices: Optional[str] = None
    splenomegaly: Optional[bool] = None

    bilirubin_level: Optional[float] = Field(default=None, ge=0)
    albumin_level: Optional[float] = Field(default=None, ge=0)
    inr: Optional[float] = Field(default=None, ge=0)
    creatinine: Optional[float] = Field(default=None, ge=0)
    platelets: Optional[int] = Field(default=None, ge=0)
    hemoglobin: Optional[float] = Field(default=None, ge=0)

    biomarkers: Optional[Dict[str, float]] = None
    imaging_findings: Optional[List[ImagingFinding]] = None

    biopsy_performed: Optional[bool] = None
    histology: Optional[Histology] = None

    liver_reserve: Optional[str] = None
    estimated_future_liver_remnant: Optional[float] = Field(default=None, ge=0, le=100)
    icg_retention_15min: Optional[float] = Field(default=None, ge=0, le=100)


class SelectedGoal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    priority: Priority
    subGoalsCount: Optional[int] = Field(default=None, ge=0)


class TreatmentGoalsData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    defineGoals: Optional[bool] = None
    equallyImportant: Optional[bool] = None
    selectedGoals: List[SelectedGoal] = Field(default_factory=list)
    priorityById: Dict[str, Priority] = Field(default_factory=dict)

    @field_validator("priorityById")
    @classmethod
    def _priority_map_not_none(cls, v: Dict[str, Priority]) -> Dict[str, Priority]:
        return v or {}


class DecisionStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    question: str
    answer: str


class ClinicalDecisionData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resultLabel: Optional[str] = None
    stageLabel: Optional[str] = None
    fto: Optional[str] = None
    finalId: Optional[str] = None
    path: List[DecisionStep] = Field(default_factory=list)


class CaseFormData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patientsContext: Optional[PatientsContext] = None
    clinicalContext: Optional[ClinicalContext] = None
    treatmentGoals: Optional[TreatmentGoalsData] = None
    clinicalDecision: Optional[ClinicalDecisionData] = None


class IngestCaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: Optional[str] = Field(default=None, description="Si viene vacío, el backend genera uno.")
    data: CaseFormData
    upsert: bool = True


class IngestCaseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    case_id: str
    received_at: datetime = Field(default_factory=datetime.utcnow)
    data: CaseFormData


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None


class SectionName(str, Enum):
    patientsContext = "patientsContext"
    clinicalContext = "clinicalContext"
    treatmentGoals = "treatmentGoals"
    clinicalDecision = "clinicalDecision"


SectionData = Union[PatientsContext, ClinicalContext, TreatmentGoalsData, ClinicalDecisionData]


class GetSectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    case_id: str
    section: SectionName
    data: Optional[SectionData] = None
    received_at: datetime = Field(default_factory=datetime.utcnow)


class CaseStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    case_id: str

    current_step: Optional[SectionName] = None
    completed_steps: List[SectionName] = Field(default_factory=list)

    missing_required: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    locked: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SubmitCaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    validate_only: bool = False


class SubmitCaseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    case_id: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    missing_required: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    locked: bool = False


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    changed_at: datetime
    changed_by: str
    field_path: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    source: Optional[Literal["manual", "import", "llm", "rules", "system"]] = None
    reason: Optional[str] = None


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    case_id: str
    events: List[AuditEvent] = Field(default_factory=list)


class TraceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    case_id: str
    owner_user_id: str
    created_at: datetime
    updated_at: datetime
    schema_version: Optional[str] = None
    engine_version: Optional[str] = None
    prompt_version: Optional[str] = None
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None


class ReportSectionStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completed: bool
    missing_required: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class CaseReportNarrative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_overview: str
    clinical_overview: str
    treatment_goals_overview: Optional[str] = None
    decision_overview: Optional[str] = None


class CaseReportAggregates(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: Optional[int] = None
    gender: Optional[str] = None
    performance_status: Optional[str] = None
    comorbidities: List[str] = Field(default_factory=list)

    bclc_stage: Optional[str] = None
    child_pugh: Optional[str] = None
    meld: Optional[int] = None

    tumor_summary: Optional[str] = None
    labs_summary: Optional[str] = None
    biomarkers_summary: Optional[str] = None

    top_goals: List[str] = Field(default_factory=list)
    mid_goals: List[str] = Field(default_factory=list)
    low_goals: List[str] = Field(default_factory=list)

    fto: Optional[str] = None
    final_id: Optional[str] = None
    stage_label: Optional[str] = None
    result_label: Optional[str] = None


class CaseReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    case_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    sections_status: Dict[SectionName, ReportSectionStatus]
    narrative: CaseReportNarrative
    aggregates: CaseReportAggregates

    decision_path: Optional[List[DecisionStep]] = None
    trace: Optional[TraceResponse] = None
    audit_log: Optional[List[AuditEvent]] = None
    raw: Optional[CaseFormData] = None


class LockResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    case_id: str
    locked: bool
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DeleteResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    case_id: str
    deleted_at: datetime = Field(default_factory=datetime.utcnow)
