from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_homepage(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"] == activities["Chess Club"]


def test_signup_adds_participant(client):
    email = "new-student@mergington.edu"
    response = client.post("/activities/Soccer%20Team/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Soccer Team"
    assert email in activities["Soccer Team"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    email = "new-student@mergington.edu"
    url = "/activities/Soccer%20Team/signup"
    client.post(url, params={"email": email})

    response = client.post(url, params={"email": email})

    assert response.status_code == 400
    assert activities["Soccer Team"]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "new-student@mergington.edu"},
    )

    assert response.status_code == 404


def test_unregister_removes_participant(client):
    activity_name = "Soccer Team"
    email = "student@mergington.edu"
    activities[activity_name]["participants"].append(email)
    url = (
        f"/activities/{quote(activity_name, safe='')}"
        f"/participants/{quote(email, safe='')}"
    )

    response = client.delete(url)

    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity_name}"
    assert email not in activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Club/participants/student%40mergington.edu"
    )

    assert response.status_code == 404


def test_unregister_rejects_unregistered_participant(client):
    response = client.delete(
        "/activities/Soccer%20Team/participants/student%40mergington.edu"
    )

    assert response.status_code == 404
