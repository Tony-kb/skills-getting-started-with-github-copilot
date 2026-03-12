import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


client = TestClient(app)


class TestGetRoot:
    def test_root_redirects_to_index(self):
        # Arrange — no setup needed

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    def test_returns_all_activities(self):
        # Arrange — no setup needed

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_activity_has_required_fields(self):
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for name, details in data.items():
            assert required_fields.issubset(details.keys()), f"{name} missing fields"


class TestSignup:
    def test_signup_success(self):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert email in activities[activity_name]["participants"]

    def test_signup_nonexistent_activity(self):
        # Arrange
        activity_name = "Nonexistent"
        email = "test@mergington.edu"

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_email(self):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # already registered

        # Act
        response = client.post(f"/activities/{activity_name}/signup?email={email}")

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"


class TestUnregister:
    def test_unregister_success(self):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # currently registered

        # Act
        response = client.request(
            "DELETE", f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert email not in activities[activity_name]["participants"]

    def test_unregister_nonexistent_activity(self):
        # Arrange
        activity_name = "Nonexistent"
        email = "test@mergington.edu"

        # Act
        response = client.request(
            "DELETE", f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_signed_up(self):
        # Arrange
        activity_name = "Chess Club"
        email = "nobody@mergington.edu"  # not registered

        # Act
        response = client.request(
            "DELETE", f"/activities/{activity_name}/unregister?email={email}"
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"
