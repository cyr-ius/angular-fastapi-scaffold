from fastapi.testclient import TestClient


def test_serves_index_for_client_routes(client: TestClient) -> None:
    response = client.get("/some/angular/route")
    assert response.status_code == 200
    assert "<app-root>" in response.text


def test_serves_static_files(client: TestClient) -> None:
    assert "console.log" in client.get("/main.js").text


def test_unknown_api_path_is_not_the_spa(client: TestClient) -> None:
    assert client.get("/api/unknown").status_code == 404


def test_path_traversal_never_leaves_the_frontend(client: TestClient) -> None:
    for path in ("/../secret.txt", "/%2e%2e/secret.txt", "/..%2fsecret.txt"):
        response = client.get(path)
        assert "secret" not in response.text, path
