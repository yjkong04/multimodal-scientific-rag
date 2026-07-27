"""Smoke tests for the /ask contract.

These lock in the two behaviors that matter most: a supported question gets a
cited answer, and an unsupported one refuses. The Week 5 eval harness builds on
this same shape.
"""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_answerable_question_is_cited():
    r = client.post("/ask", json={"question": "What does the figure show about dose and response?"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "answered"
    assert body["citations"], "an answered question must carry citations"
    # At least one figure citation for a figure question.
    assert any(c["modality"] == "figure" for c in body["citations"])
    # Every citation resolves to a source.
    assert all(c["paper_id"] and c["source_id"] for c in body["citations"])


def test_unsupported_question_refuses():
    r = client.post("/ask", json={"question": "quantum chromodynamics lattice gauge theory"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "refused"
    assert body["citations"] == []


def test_question_too_short_is_rejected():
    r = client.post("/ask", json={"question": "hi"})
    assert r.status_code == 422
