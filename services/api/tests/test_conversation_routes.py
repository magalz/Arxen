"""Route behavior at the repository boundary; SQL is tested only in PostgreSQL."""

from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from arxen_api.contracts import Message
from arxen_api.conversation import MessageConflict
from arxen_api.conversation_api import create_conversation_router


@pytest.mark.parametrize("created", [True, False])
def test_submission_uses_validated_identity_and_exits_transaction_before_success(
    created,
):
    owner, case, key = uuid4(), uuid4(), uuid4()
    message = Message(
        id=uuid4(),
        case_id=case,
        sequence=7,
        role="user",
        content="  Test\n🧪 ",
        created_at=datetime.now(UTC),
    )
    calls, closed, observed = [], [], []

    class Repository:
        def submit_owned_message(self, *args):
            calls.append(args)
            return message, created

    @contextmanager
    def repository():
        yield Repository()
        closed.append(True)

    application = FastAPI()
    application.include_router(
        create_conversation_router(lambda: owner, repository), prefix="/api/v1"
    )

    async def probe(scope, receive, send):
        async def inspect(event):
            if event["type"] == "http.response.start":
                observed.append(bool(closed))
            await send(event)

        await application(scope, receive, inspect)

    with TestClient(probe) as client:
        response = client.post(
            f"/api/v1/cases/{case}/messages",
            json={"client_message_id": str(key), "content": message.content},
            headers={"Idempotency-Key": str(key), "X-User-Id": str(uuid4())},
        )
    assert response.status_code == (201 if created else 200)
    assert response.json()["id"] == str(message.id)
    assert response.json()["content"] == message.content
    assert response.headers["cache-control"] == "no-store"
    assert calls == [(owner, case, key, message.content)]
    assert observed == [True]


@pytest.mark.parametrize("outcome,status", [(None, 404), ("conflict", 409)])
def test_submission_rejection_has_stable_error(outcome, status):
    class Repository:
        def submit_owned_message(self, *args):
            if outcome == "conflict":
                raise MessageConflict("private payload")
            return None

    @contextmanager
    def repository():
        yield Repository()

    app = FastAPI()
    app.include_router(create_conversation_router(uuid4, repository), prefix="/api/v1")
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/cases/{uuid4()}/messages",
            json={"client_message_id": str(uuid4()), "content": "Synthetic"},
        )
    assert response.status_code == status
    assert response.json() == {
        "detail": "Case not found" if status == 404 else "Message submission conflict"
    }
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("size,limit", [(0, 2), (1, 2), (2, 2), (3, 2), (3, 50)])
def test_history_is_bounded_and_returns_next_cursor_only_when_more_exist(size, limit):
    owner, case = uuid4(), uuid4()
    messages = [
        Message(
            id=uuid4(),
            case_id=case,
            sequence=number + 4,
            role="user",
            content=f"Synthetic {number}",
            created_at=datetime.now(UTC),
        )
        for number in range(size)
    ]
    calls = []

    class Repository:
        def list_owned_messages(self, *args, **kwargs):
            calls.append((args, kwargs))
            return messages

    @contextmanager
    def repository():
        yield Repository()

    app = FastAPI()
    app.include_router(
        create_conversation_router(lambda: owner, repository), prefix="/api/v1"
    )
    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/cases/{case}/messages?after_sequence=3&limit={limit}"
        )
    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["items"]] == [
        str(message.id) for message in messages[:limit]
    ]
    assert body["next_after_sequence"] == (
        messages[limit - 1].sequence if size > limit else None
    )
    assert calls == [((owner, case), {"after_sequence": 3, "limit": limit + 1})]
    assert response.headers["cache-control"] == "no-store"


def test_inaccessible_history_is_not_an_empty_success():
    class Repository:
        def list_owned_messages(self, *args, **kwargs):
            return None

    @contextmanager
    def repository():
        yield Repository()

    app = FastAPI()
    app.include_router(create_conversation_router(uuid4, repository), prefix="/api/v1")
    with TestClient(app) as client:
        response = client.get(f"/api/v1/cases/{uuid4()}/messages")
    assert response.status_code == 404
    assert response.json() == {"detail": "Case not found"}
