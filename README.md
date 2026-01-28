# CUSE Case API (FastAPI)

API de referencia para manejar casos clínicos (CRUD, secciones, workflow, reportes, trazabilidad y auditoría) usando FastAPI y Pydantic.

## Estructura

- `app/main.py`: rutas FastAPI con toda la API.
- `app/models.py`: modelos Pydantic (inputs/outputs).
- `app/storage.py`: mock de persistencia tipo DynamoDB (in-memory JSON + audit).
- `tests/test_api.py`: tests de contrato por endpoint.

## Modelos (Pydantic)

Los modelos principales viven en `app/models.py`:

- **CaseFormData**: payload principal del caso (`patientsContext`, `clinicalContext`, `treatmentGoals`, `clinicalDecision`).
- **PatientsContext**, **ClinicalContext**, **TreatmentGoalsData**, **ClinicalDecisionData**: secciones del caso.
- **IngestCaseResponse**, **GetSectionResponse**, **CaseStatusResponse**, **SubmitCaseResponse**: respuestas de ingesta/flujo.
- **CaseReportResponse**: reporte agregado del caso.
- **AuditLogResponse** y **TraceResponse**: trazabilidad/auditoría.
- **LockResponse** y **DeleteResponse**: control de bloqueo/eliminación.
- **ErrorResponse**: errores estandarizados.

## Endpoints

> Nota: todos los endpoints retornan `ErrorResponse` para errores. Consultar `app/models.py` para los esquemas.

### 1) Create case
**POST** `/cases`
- **Input**: `CaseFormData`
- **Output**: `IngestCaseResponse`
- **Descripción**: crea un case asociado al usuario y retorna `case_id`.

### 2) Upsert case
**PUT** `/cases/{case_id}`
- **Input**: `CaseFormData`
- **Output**: `IngestCaseResponse`
- **Descripción**: reemplaza/actualiza el Case Form Data completo.

### 3) Patch secciones
**PATCH** `/cases/{case_id}/patients-context`
- **Input**: `PatientsContext`
- **Output**: `IngestCaseResponse`

**PATCH** `/cases/{case_id}/clinical-context`
- **Input**: `ClinicalContext`
- **Output**: `IngestCaseResponse`

**PATCH** `/cases/{case_id}/treatment-goals`
- **Input**: `TreatmentGoalsData`
- **Output**: `IngestCaseResponse`

**PATCH** `/cases/{case_id}/clinical-decision`
- **Input**: `ClinicalDecisionData`
- **Output**: `IngestCaseResponse`

### 4) Read case
**GET** `/cases/{case_id}`
- **Input**: none
- **Output**: `CaseFormData`

**GET** `/cases/{case_id}/section/{section_name}`
- **Input**: `section_name` (`SectionName`)
- **Output**: `GetSectionResponse`

### 5) Workflow / validation
**GET** `/cases/{case_id}/status`
- **Input**: none
- **Output**: `CaseStatusResponse`

**POST** `/cases/{case_id}/submit`
- **Input**: `SubmitCaseRequest`
- **Output**: `SubmitCaseResponse`

### 6) Report agregado
**GET** `/cases/{case_id}/report`
- **Input**: query params opcionales `include_trace`, `include_audit`, `include_raw`, `format`
- **Output**: `CaseReportResponse`

### 7) Traceability
**GET** `/cases/{case_id}/audit-log`
- **Input**: none
- **Output**: `AuditLogResponse`

**GET** `/cases/{case_id}/trace`
- **Input**: none
- **Output**: `TraceResponse`

### 8) Lock control
**POST** `/cases/{case_id}/lock`
- **Input**: none
- **Output**: `LockResponse`

**POST** `/cases/{case_id}/unlock`
- **Input**: none
- **Output**: `LockResponse`

### 9) Delete
**DELETE** `/cases/{case_id}`
- **Input**: none
- **Output**: `DeleteResponse`

## Ejecutar tests

```bash
pytest -q
```

> Nota: necesitas dependencias como `fastapi` y `pytest` instaladas en tu entorno.
