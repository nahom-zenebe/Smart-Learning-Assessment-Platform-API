"""API tests for /notifications (auth simulated via test headers).

The fake auth middleware in conftest.py injects the user that the real
``get_current_user`` / ``require_roles`` dependencies read, so role rules
and ownership guards are exercised end to end.
"""

import pytest

MISSING_ID = "64b1f0c0a1b2c3d4e5f60718"

STUDENT = {"x-test-user-id": "student-1", "x-test-role": "student"}
OTHER_STUDENT = {"x-test-user-id": "student-2", "x-test-role": "student"}
INSTRUCTOR = {"x-test-user-id": "instructor-1", "x-test-role": "instructor"}
ADMIN = {"x-test-user-id": "admin-1", "x-test-role": "admin"}


def create_notification(api, user_id="student-1", title="Hello", headers=INSTRUCTOR):
    response = api.post(
        "/notifications/",
        json={
            "user_id": user_id,
            "title": title,
            "message": "Some message",
            "type": "info",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_requires_instructor_or_admin_role(api):
    response = api.post(
        "/notifications/",
        json={"user_id": "student-1", "title": "t", "message": "m"},
        headers=STUDENT,
    )
    assert response.status_code == 403


def test_instructor_can_create_notification(api):
    notification = create_notification(api)

    assert notification["id"]
    assert notification["user_id"] == "student-1"
    assert notification["read"] is False
    assert notification["type"] == "info"


def test_list_returns_only_own_notifications(api):
    create_notification(api, title="First notification")
    create_notification(api, title="Second notification")
    create_notification(api, user_id="student-2", title="Someone else notification")

    response = api.get("/notifications/", headers=STUDENT)

    assert response.status_code == 200
    notifications = response.json()
    assert len(notifications) == 2
    assert all(n["user_id"] == "student-1" for n in notifications)


def test_unread_count(api):
    create_notification(api, title="First notification")
    create_notification(api, title="Second notification")

    response = api.get("/notifications/unread-count", headers=STUDENT)

    assert response.status_code == 200
    assert response.json() == {"count": 2}


def test_mark_all_read(api):
    create_notification(api, title="First notification")
    create_notification(api, title="Second notification")

    response = api.patch("/notifications/read-all", headers=STUDENT)
    assert response.status_code == 200
    assert response.json() == {"modified": 2}

    count = api.get("/notifications/unread-count", headers=STUDENT).json()
    assert count == {"count": 0}


def test_get_notification_as_owner(api):
    notification = create_notification(api)

    response = api.get(f"/notifications/{notification['id']}", headers=STUDENT)

    assert response.status_code == 200
    assert response.json()["id"] == notification["id"]


def test_cannot_read_someone_elses_notification(api):
    notification = create_notification(api, user_id="student-1")

    response = api.get(f"/notifications/{notification['id']}", headers=OTHER_STUDENT)

    assert response.status_code == 403


def test_admin_can_read_any_notification(api):
    notification = create_notification(api, user_id="student-1")

    response = api.get(f"/notifications/{notification['id']}", headers=ADMIN)

    assert response.status_code == 200


def test_mark_single_notification_read(api):
    notification = create_notification(api)

    response = api.patch(f"/notifications/{notification['id']}/read", headers=STUDENT)

    assert response.status_code == 200
    assert response.json()["read"] is True


def test_delete_notification(api):
    notification = create_notification(api)

    response = api.delete(f"/notifications/{notification['id']}", headers=STUDENT)

    assert response.status_code == 200
    assert response.json()["id"] == notification["id"]
    assert (
        api.get(f"/notifications/{notification['id']}", headers=STUDENT).status_code
        == 404
    )


def test_get_missing_notification_returns_404(api):
    response = api.get(f"/notifications/{MISSING_ID}", headers=STUDENT)
    assert response.status_code == 404


def test_requires_authentication(api):
    response = api.get("/notifications/")  # no test headers -> no user
    assert response.status_code == 401
