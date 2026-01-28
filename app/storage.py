from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from .models import (
    AuditEvent,
    CaseFormData,
    ClinicalContext,
    ClinicalDecisionData,
    PatientsContext,
    SectionName,
    TreatmentGoalsData,
)


@dataclass
class CaseRecord:
    case_id: str
    data: CaseFormData
    owner_user_id: str
    created_at: datetime
    updated_at: datetime
    locked: bool = False
    deleted: bool = False
    schema_version: Optional[str] = None
    engine_version: Optional[str] = None
    prompt_version: Optional[str] = None
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    audit_log: List[AuditEvent] = field(default_factory=list)


class CaseRepository:
    def __init__(self) -> None:
        self._cases: Dict[str, CaseRecord] = {}

    def create_case(self, data: CaseFormData, owner_user_id: str) -> CaseRecord:
        case_id = str(uuid4())
        now = datetime.utcnow()
        record = CaseRecord(
            case_id=case_id,
            data=data,
            owner_user_id=owner_user_id,
            created_at=now,
            updated_at=now,
        )
        self._cases[case_id] = record
        self._record_audit(record, "case", None, data.model_dump(mode="json"), "system")
        return record

    def get_case(self, case_id: str) -> Optional[CaseRecord]:
        record = self._cases.get(case_id)
        if record and not record.deleted:
            return record
        return None

    def delete_case(self, case_id: str, actor: str) -> Optional[CaseRecord]:
        record = self._cases.get(case_id)
        if not record or record.deleted:
            return None
        record.deleted = True
        record.updated_at = datetime.utcnow()
        self._record_audit(record, "case", record.data.model_dump(mode="json"), None, actor)
        return record

    def upsert_case(self, case_id: str, data: CaseFormData, actor: str) -> Optional[CaseRecord]:
        record = self._cases.get(case_id)
        if not record or record.deleted:
            return None
        old = record.data.model_dump(mode="json")
        record.data = data
        record.updated_at = datetime.utcnow()
        self._record_audit(record, "case", old, data.model_dump(mode="json"), actor)
        return record

    def update_section(
        self,
        case_id: str,
        section: SectionName,
        section_data: PatientsContext | ClinicalContext | TreatmentGoalsData | ClinicalDecisionData,
        actor: str,
    ) -> Optional[CaseRecord]:
        record = self._cases.get(case_id)
        if not record or record.deleted:
            return None
        field_path = section.value
        old_section = getattr(record.data, field_path)
        setattr(record.data, field_path, section_data)
        record.updated_at = datetime.utcnow()
        self._record_audit(
            record,
            field_path,
            old_section.model_dump(mode="json") if old_section else None,
            section_data.model_dump(mode="json"),
            actor,
        )
        return record

    def set_lock(self, case_id: str, locked: bool, actor: str) -> Optional[CaseRecord]:
        record = self._cases.get(case_id)
        if not record or record.deleted:
            return None
        old_value = record.locked
        record.locked = locked
        record.updated_at = datetime.utcnow()
        self._record_audit(record, "locked", old_value, locked, actor)
        return record

    def _record_audit(
        self,
        record: CaseRecord,
        field_path: str,
        old_value: object,
        new_value: object,
        actor: str,
        source: str | None = "system",
    ) -> None:
        record.audit_log.append(
            AuditEvent(
                changed_at=datetime.utcnow(),
                changed_by=actor,
                field_path=field_path,
                old_value=old_value,
                new_value=new_value,
                source=source,
            )
        )
