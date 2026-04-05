import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

from app import app

HISTORY_FILE = Path("command_history.json")


@pytest.fixture(autouse=True)
def cleanup_history():
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
    with app.test_client() as tmp_client:
        tmp_client.post("/api/reset")
        tmp_client.post("/api/chain/reset")
    yield
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_parse_endpoint(client):
    response = client.post(
        "/api/parse",
        data=json.dumps({"command": "move forward 20 cm"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["action"] == "move"
    assert body["direction"] == "forward"
    assert body["distance_cm"] == 20.0


def test_execute_endpoint(client):
    response = client.post(
        "/api/execute",
        data=json.dumps({
            "action": "move",
            "direction": "forward",
            "distance_cm": 15.0,
            "raw": "move forward 15 cm",
        }),
        content_type="application/json",
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert any("Moved forward" in line for line in body["output"])


def test_chain_parse_and_execute(client):
    response = client.post(
        "/api/chain/parse",
        data=json.dumps({"command": "move forward and rotate right 90 degrees and grab"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["is_chain"] is True
    assert body["total_steps"] == 3
    assert body["commands"][0]["action"] == "move"
    assert body["commands"][1]["action"] == "rotate"
    assert body["commands"][2]["action"] == "grab"

    # Execute first step
    step = body["commands"][0]
    exec_response = client.post(
        "/api/chain/execute",
        data=json.dumps(step),
        content_type="application/json",
    )
    assert exec_response.status_code == 200
    exec_body = exec_response.get_json()
    assert exec_body["success"] is True
    assert exec_body["chain_progress"]["current_step"] == 1


def test_status_and_visualize(client):
    client.post(
        "/api/execute",
        data=json.dumps({"action": "move", "direction": "left", "distance_cm": 5.0, "raw": "move left 5 cm"}),
        content_type="application/json",
    )
    status_response = client.get("/api/status")
    assert status_response.status_code == 200
    status_body = status_response.get_json()
    assert status_body["x"] == -5.0
    assert status_body["y"] == 0.0

    svg_response = client.get("/api/visualize")
    assert svg_response.status_code == 200
    assert b"<svg" in svg_response.data


def test_speech_status_endpoint(client):
    response = client.get("/api/speech/status")
    assert response.status_code == 200
    body = response.get_json()
    assert "web_speech_api" in body
    assert body["web_speech_api"]["available"] is True
