"""Exercise uploads through the same browser API used by Ground truth."""

from datetime import datetime
from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
from pypdfium2 import PdfDocument
import pytest

from codeanvil.UI.ui import create_app

API = "/api/workspace/build-package"
ORIGIN = {"origin": "http://localhost"}


@pytest.fixture
def workspace(tmp_path):
    gt = tmp_path / ".codeanvil/GT"
    gt.mkdir(parents=True)
    (gt.parent / "project.yaml").write_text("id: build-package-fixture\nname: Build Package test\n")
    (gt / "build_package.md").write_text("# S0 source")
    with TestClient(create_app(tmp_path), base_url="http://localhost") as client:
        yield client, gt


def _zip(members):
    data = BytesIO()
    with ZipFile(data, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)
    return data.getvalue()


def _url(file, action="preview"):
    return f"{API}/{file['batch']}/{file['index']}/{action}"


def test_uploads_are_listed_with_dates_and_archive_member_paths(workspace):
    client, gt = workspace
    archive = _zip({"manual/gain.csv": "channel;gain\n1;5\n", "notes/readme.md": "# Receiver"})
    response = client.post(API, files=[
        ("files", ("Build package.md", b"# Uploaded requirements")),
        ("files", ("manual.zip", archive)),
        ("files", ("app.html", b"<script>this is plain text</script>")),
    ], headers=ORIGIN)
    assert response.status_code == 201, response.text
    items = response.json()["files"]
    listed = client.get(API).json()["files"]
    assert listed[:-1] == items
    assert listed[-1]["path"] == "build_package.md"
    assert [(item["name"], item["archive"]) for item in items] == [
        ("Build package.md", None), ("manual/gain.csv", "manual.zip"),
        ("notes/readme.md", "manual.zip"), ("app.html", None),
    ]
    assert all(datetime.fromisoformat(item["uploaded_at"]).utcoffset() is not None for item in items)
    assert client.get(_url(items[1])).json()["rows"] == [["channel", "gain"], ["1", "5"]]
    assert client.get(_url(items[2])).json() == {"format": "markdown", "content": "# Receiver", "clipped": False}
    assert client.get(_url(items[3])).json()["format"] == "text"
    assert (gt / "build_package.md").read_text() == "# S0 source"


def test_denies_foreign_origin_and_rolls_back_invalid_archive(workspace):
    client, gt = workspace
    archive = _zip({"valid.txt": "valid", "../outside.txt": "must not be written"})
    files = [("files", ("package.zip", archive))]
    assert client.post(API, files=files, headers={"origin": "http://localhost:1234"}).status_code == 403
    assert client.post(API, files=files, headers=ORIGIN).status_code == 422
    assert [item["path"] for item in client.get(API).json()["files"]] == ["build_package.md"]
    assert not list((gt / "build_package_uploads").iterdir())
    assert not (gt / "outside.txt").exists()


def test_pdf_pages_are_embedded_as_images(workspace):
    client, gt = workspace
    path = gt / "reference.pdf"
    with PdfDocument.new() as document:
        document.new_page(100, 200)
        document.new_page(200, 100)
        document.save(path)
    response = client.post(API, files=[("files", ("Example.pdf", path.read_bytes()))], headers=ORIGIN)
    assert response.status_code == 201, response.text
    file, = response.json()["files"]
    assert client.get(_url(file)).json() == {"format": "pdf", "pages": 2}
    second = client.get(_url(file, "pdf-page"), params={"page": 2})
    assert second.headers["content-type"] == "image/png"
    assert second.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert client.get(_url(file, "pdf-page"), params={"page": 3}).status_code == 404
    scanned = client.get(f"{API}/existing/pdf-page", params={"path": "reference.pdf", "page": 2})
    assert scanned.status_code == 200
    assert scanned.content == second.content


def test_disk_sources_and_generated_gt_pair_are_visible_after_they_are_written(workspace):
    client, gt = workspace
    before = client.get("/api/workspace/overview").json()
    assert not any(item["exists"] for item in before["artifacts"] if item["path"].endswith(("StRS.md", "SyRS.md")))

    (gt / "annexes").mkdir()
    (gt / "annexes/Plant settings.csv").write_text("valve,gain\n1,5\n")
    (gt / "StRS.md").write_text("# Generated StRS")
    (gt / "SyRS.md").write_text("# Generated SyRS")
    files = {item["path"]: item for item in client.get(API).json()["files"]}
    assert set(files) == {"build_package.md", "annexes/Plant settings.csv"}
    assert datetime.fromisoformat(files["annexes/Plant settings.csv"]["modified_at"]).utcoffset() is not None
    preview = client.get(f"{API}/existing/preview", params={"path": "annexes/Plant settings.csv"})
    assert preview.json()["rows"] == [["valve", "gain"], ["1", "5"]]
    for name in ("StRS", "SyRS"):
        path = f".codeanvil/GT/{name}.md"
        artifact = next(item for item in client.get("/api/workspace/overview").json()["artifacts"] if item["path"] == path)
        assert artifact["exists"] and name in artifact["label"]
        assert client.get("/api/workspace/artifact", params={"path": path}).json()["content"] == f"# Generated {name}"
        assert client.get(f"{API}/existing/preview", params={"path": f"{name}.md"}).status_code == 404


def test_ignores_external_links_when_scanning_and_previewing(workspace):
    client, gt = workspace
    outside = gt.parent.parent / "outside.md"
    outside.write_text("Outside Ground Truth")
    try:
        (gt / "linked.md").symlink_to(outside)
    except OSError:
        pytest.skip("symbolic links are unavailable")
    assert [item["path"] for item in client.get(API).json()["files"]] == ["build_package.md"]
    assert client.get(f"{API}/existing/preview", params={"path": "linked.md"}).status_code == 400
