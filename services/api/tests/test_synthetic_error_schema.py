"""OpenAPI must describe the error bodies actually returned by synthetic routes."""

import pytest

from arxen_api.main import create_app


@pytest.mark.parametrize(
    "path,method,status",
    [
        ("/api/v1/me", "get", 401),
        ("/api/v1/cases", "post", 401),
        ("/api/v1/cases", "post", 422),
        ("/api/v1/cases", "post", 503),
        ("/api/v1/cases/{case_id}", "get", 401),
        ("/api/v1/cases/{case_id}", "get", 404),
        ("/api/v1/cases/{case_id}", "get", 422),
        ("/api/v1/cases/{case_id}", "get", 503),
    ],
)
def test_error_response_schema_matches_the_returned_detail_string(
    path, method, status
) -> None:
    application = create_app(
        {
            "ARXEN_ENV": "test",
            "ARXEN_SYNTHETIC_AUTH_ENABLED": "true",
            "ARXEN_SYNTHETIC_USER_ID": "30397fef-c76f-4a0f-bc8c-b453ce1d23a9",
            "ARXEN_SYNTHETIC_TOKEN": "synthetic-schema-token",
            "DATABASE_URL": "postgresql://example.invalid/synthetic",
        }
    )
    schema = application.openapi()
    response = schema["paths"][path][method]["responses"].get(str(status))
    assert response is not None, f"HTTP {status} is missing from the error contract"
    body = response["content"]["application/json"]["schema"]
    if "$ref" in body:
        body = schema["components"]["schemas"][body["$ref"].rsplit("/", 1)[-1]]
    assert body["type"] == "object"
    assert set(body["properties"]) == {"detail"}
    assert body["properties"]["detail"]["type"] == "string"
