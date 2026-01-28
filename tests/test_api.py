from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_case_payload():
    return {
        "patientsContext": {"age": 45, "gender": "female"},
        "clinicalContext": {"tumor_location": "liver", "barcelona_stage": "B"},
        "treatmentGoals": {
            "defineGoals": True,
            "selectedGoals": [
                {"id": "goal-1", "label": "Curación", "priority": "top"},
                {"id": "goal-2", "label": "Calidad de vida", "priority": "mid"},
            ],
            "priorityById": {"goal-1": "top", "goal-2": "mid"},
        },
        "clinicalDecision": {
            "resultLabel": "Proceder",
            "stageLabel": "Stage B",
            "fto": "TACE",
            "finalId": "decision-123",
            "path": [{"id": "step-1", "question": "Q1", "answer": "A1"}],
        },
    }


def create_case():
    response = client.post("/cases", json=create_case_payload())
    assert response.status_code == 200
    return response.json()["case_id"]


def test_create_case():
    response = client.post("/cases", json=create_case_payload())
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["case_id"]
    assert data["data"]["patientsContext"]["age"] == 45


def test_upsert_case():
    case_id = create_case()
    payload = create_case_payload()
    payload["patientsContext"]["age"] = 50
    response = client.put(f"/cases/{case_id}", json=payload)
    assert response.status_code == 200
    assert response.json()["data"]["patientsContext"]["age"] == 50


def test_patch_patients_context():
    case_id = create_case()
    response = client.patch(f"/cases/{case_id}/patients-context", json={"age": 60})
    assert response.status_code == 200
    assert response.json()["data"]["patientsContext"]["age"] == 60


def test_patch_clinical_context():
    case_id = create_case()
    response = client.patch(
        f"/cases/{case_id}/clinical-context", json={"tumor_location": "hepatic"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["clinicalContext"]["tumor_location"] == "hepatic"


def test_patch_treatment_goals():
    case_id = create_case()
    response = client.patch(
        f"/cases/{case_id}/treatment-goals",
        json={
            "defineGoals": False,
            "selectedGoals": [{"id": "goal-3", "label": "Control", "priority": "low"}],
            "priorityById": {"goal-3": "low"},
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["treatmentGoals"]["selectedGoals"][0]["id"] == "goal-3"


def test_patch_clinical_decision():
    case_id = create_case()
    response = client.patch(
        f"/cases/{case_id}/clinical-decision",
        json={
            "resultLabel": "Evaluar",
            "stageLabel": "Stage A",
            "path": [{"id": "step-2", "question": "Q2", "answer": "A2"}],
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["clinicalDecision"]["stageLabel"] == "Stage A"


def test_get_case():
    case_id = create_case()
    response = client.get(f"/cases/{case_id}")
    assert response.status_code == 200
    assert response.json()["patientsContext"]["age"] == 45


def test_get_case_section():
    case_id = create_case()
    response = client.get(f"/cases/{case_id}/section/patientsContext")
    assert response.status_code == 200
    assert response.json()["section"] == "patientsContext"


def test_get_case_status():
    case_id = create_case()
    response = client.get(f"/cases/{case_id}/status")
    assert response.status_code == 200
    data = response.json()
    assert "patientsContext" in data["completed_steps"]


def test_submit_case():
    case_id = create_case()
    response = client.post(f"/cases/{case_id}/submit", json={"validate_only": True})
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_get_case_report():
    case_id = create_case()
    response = client.get(
        f"/cases/{case_id}/report",
        params={"include_trace": True, "include_audit": True, "include_raw": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == case_id
    assert data["trace"]["owner_user_id"] == "user-123"
    assert data["raw"]["patientsContext"]["age"] == 45


def test_get_case_audit_log():
    case_id = create_case()
    response = client.get(f"/cases/{case_id}/audit-log")
    assert response.status_code == 200
    assert response.json()["case_id"] == case_id


def test_get_case_trace():
    case_id = create_case()
    response = client.get(f"/cases/{case_id}/trace")
    assert response.status_code == 200
    assert response.json()["case_id"] == case_id


def test_lock_unlock_case():
    case_id = create_case()
    lock_response = client.post(f"/cases/{case_id}/lock")
    assert lock_response.status_code == 200
    assert lock_response.json()["locked"] is True
    unlock_response = client.post(f"/cases/{case_id}/unlock")
    assert unlock_response.status_code == 200
    assert unlock_response.json()["locked"] is False


def test_delete_case():
    case_id = create_case()
    response = client.delete(f"/cases/{case_id}")
    assert response.status_code == 200
    follow_up = client.get(f"/cases/{case_id}")
    assert follow_up.status_code == 404
