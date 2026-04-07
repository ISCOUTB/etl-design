"""Tests for events routes."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from src import models
from src.api.deps import get_idempotency_service
from src.main import app


@pytest.fixture
def mock_idempotency_service():
    service = Mock()
    service.get_task_by_id = Mock(return_value=None)
    service.update_task_status = Mock(return_value=None)
    return service


@pytest.fixture
def events_client(test_client: TestClient, mock_idempotency_service):
    app.dependency_overrides[get_idempotency_service] = lambda: mock_idempotency_service
    try:
        yield test_client
    finally:
        app.dependency_overrides.pop(get_idempotency_service, None)


class TestEventsRoutes:
    def test_task_completed_not_found(
        self, events_client: TestClient, mock_idempotency_service
    ):
        mock_idempotency_service.get_task_by_id.return_value = None

        response = events_client.post(
            "/api/v1/events/task-completed",
            json={
                "task_id": "task-1",
                "idempotency_key": "key-1",
                "status": "success",
                "message": "done",
                "raw_data": {"a": 1},
            },
        )

        assert response.status_code == 200
        assert response.json()["code"] == 404
        assert response.json()["status"] == "task-not-found"

    def test_task_completed_already_processed(
        self, events_client: TestClient, mock_idempotency_service
    ):
        mock_idempotency_service.get_task_by_id.return_value = SimpleNamespace(
            status=models.TaskStatus.COMPLETED
        )

        response = events_client.post(
            "/api/v1/events/task-completed",
            json={
                "task_id": "task-2",
                "idempotency_key": "key-2",
                "status": "success",
                "message": "done",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "already-processed"
        assert response.json()["data"]["task_id"] == "task-2"

    def test_task_completed_update_failed(
        self, events_client: TestClient, mock_idempotency_service
    ):
        mock_idempotency_service.get_task_by_id.return_value = SimpleNamespace(
            status=models.TaskStatus.PENDING
        )
        mock_idempotency_service.update_task_status.side_effect = RuntimeError("boom")

        response = events_client.post(
            "/api/v1/events/task-completed",
            json={
                "task_id": "task-3",
                "idempotency_key": "key-3",
                "status": "failed",
                "message": "error",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "update-failed"
        assert response.json()["code"] == 500

    def test_task_completed_success(
        self, events_client: TestClient, mock_idempotency_service
    ):
        mock_idempotency_service.get_task_by_id.return_value = SimpleNamespace(
            status=models.TaskStatus.PENDING
        )

        response = events_client.post(
            "/api/v1/events/task-completed",
            json={
                "task_id": "task-4",
                "idempotency_key": "key-4",
                "status": "success",
                "message": "ok",
                "raw_data": {"rows": 10},
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "received-request"
        assert response.json()["data"]["task_id"] == "task-4"
