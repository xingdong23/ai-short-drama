from fastapi.testclient import TestClient

from api.app import app


client = TestClient(app)


def test_debug_ui_route_serves_html() -> None:
    response = client.get("/debug")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AI短剧调试控制台" in response.text
    assert "怎么使用" in response.text
    assert "script" in response.text
    assert "character" in response.text
    assert "video" in response.text
    assert "voice" in response.text
    assert "compose" in response.text
    assert "/debug/assets/app.js" in response.text


def test_debug_ui_asset_route_serves_javascript() -> None:
    response = client.get("/debug/assets/app.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert "const pipelineForm" in response.text
