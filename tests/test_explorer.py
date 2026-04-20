import pytest
import os
import json
import shutil
import asyncio
from pathlib import Path
from app.core.explorer import ShadowExplorer

@pytest.fixture
def workspace_setup(tmp_path):
    # Create a dummy workspace
    project1 = tmp_path / "project1"
    project1.mkdir()
    (project1 / "README.md").write_text("# Project 1")
    (project1 / "main.py").write_text("print('hello')")

    project2 = tmp_path / "project2"
    project2.mkdir()
    (project2 / "package.json").write_text('{"name": "project2"}')
    (project2 / "index.js").write_text("console.log('hello')")

    excluded = project1 / "node_modules"
    excluded.mkdir()
    (excluded / "junk.js").write_text("junk")

    return tmp_path

@pytest.mark.asyncio
async def test_rebuild_index(workspace_setup, tmp_path):
    index_file = tmp_path / "data" / "shadow_index.json"
    # Monkeypatch index_file path in ShadowExplorer instance
    explorer = ShadowExplorer(base_paths=[workspace_setup])
    explorer.index_file = index_file

    result = await explorer.rebuild_index()

    assert "✅ Indexación completada" in result
    assert index_file.exists()

    with open(index_file, "r") as f:
        data = json.load(f)

    assert "projects" in data
    assert "project1" in data["projects"]
    assert "project2" in data["projects"]
    assert data["projects"]["project2"]["type"] == "python/js"

    files = [f["name"] for f in data["files"]]
    assert "main.py" in files
    assert "index.js" in files
    assert "README.md" in files
    # package.json is NOT in the extension list, so it won't be indexed as a file
    assert "package.json" not in files
    assert "junk.js" not in files # node_modules should be excluded

@pytest.mark.asyncio
async def test_search(workspace_setup, tmp_path):
    index_file = tmp_path / "data" / "shadow_index.json"
    explorer = ShadowExplorer(base_paths=[workspace_setup])
    explorer.index_file = index_file

    await explorer.rebuild_index()

    search_result = explorer.search("main.py")
    assert "main.py" in search_result

    search_result = explorer.search("project1")
    assert "project1" in search_result

    search_result = explorer.search("nonexistent")
    assert "No encontré coincidencias exactas" in search_result
