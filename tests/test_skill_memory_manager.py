import pytest
import json
from pathlib import Path
from datetime import datetime
from app.skills import memory_manager

@pytest.fixture
def mock_memory_env(tmp_path, monkeypatch):
    """Fixture to redirect memory manager paths to a temporary directory."""
    memory_root = tmp_path / "memory"
    memory_file = memory_root / "MEMORY.md"
    entities_dir = memory_root / "entities"
    learned_dir = memory_root / "learned"

    monkeypatch.setattr(memory_manager, "MEMORY_ROOT", memory_root)
    monkeypatch.setattr(memory_manager, "MEMORY_FILE", memory_file)
    monkeypatch.setattr(memory_manager, "ENTITIES_DIR", entities_dir)
    monkeypatch.setattr(memory_manager, "LEARNED_DIR", learned_dir)

    return {
        "root": memory_root,
        "file": memory_file,
        "entities": entities_dir,
        "learned": learned_dir
    }

def test_remember(mock_memory_env):
    """Test that remember creates the file and appends entries correctly."""
    result = memory_manager.remember("test_key", "test_value", "test_cat")

    assert "✅ Memorizado: [test_cat] test_key" == result
    assert mock_memory_env["file"].exists()

    content = mock_memory_env["file"].read_text(encoding="utf-8")
    assert "# KYNIKOS Memory\n" in content
    assert "### [" in content
    assert "[TEST_CAT] test_key" in content
    assert "test_value" in content
    assert "---" in content

    # Test appending another entry
    memory_manager.remember("another_key", "another_value")
    content_updated = mock_memory_env["file"].read_text(encoding="utf-8")
    assert content_updated.count("###") == 2
    assert "[GENERAL] another_key" in content_updated

def test_recall(mock_memory_env):
    """Test searching by keyword in memory."""
    memory_manager.remember("Python", "Language for AI", "coding")
    memory_manager.remember("FastAPI", "Web framework", "coding")
    memory_manager.remember("Cancun", "A nice city", "travel")

    # Search for match
    result = memory_manager.recall("python")
    assert "🧠 **Memoria — 'python':**" in result
    assert "[CODING] Python" in result
    assert "Language for AI" in result

    # Search for multiple matches
    result_multi = memory_manager.recall("coding")
    assert "[CODING] Python" in result_multi
    assert "[CODING] FastAPI" in result_multi

    # Search case-insensitivity
    assert "[CODING] FastAPI" in memory_manager.recall("FASTAPI")

def test_recall_empty_and_no_results(mock_memory_env):
    """Test recall when memory is empty or no matches are found."""
    # File doesn't exist
    assert memory_manager.recall("anything") == "📭 Memoria vacía."

    # File exists but no match
    memory_manager.remember("key", "value")
    result = memory_manager.recall("missing")
    assert "🔍 Sin resultados para 'missing' en memoria." == result

def test_entity_management(mock_memory_env):
    """Test saving, loading, and listing entities."""
    data = {"name": "Test Hotel", "stars": 5}
    result = memory_manager.save_entity("hotel", "h123", data)

    assert "✅ Entidad guardada: hotel/h123" == result

    entity_path = mock_memory_env["entities"] / "hotel" / "h123.json"
    assert entity_path.exists()

    saved_data = json.loads(entity_path.read_text(encoding="utf-8"))
    assert saved_data["name"] == "Test Hotel"
    assert "_updated_at" in saved_data

    # Get entity
    loaded = memory_manager.get_entity("hotel", "h123")
    assert loaded["name"] == "Test Hotel"

    # Get non-existent
    assert memory_manager.get_entity("hotel", "missing") is None

    # List entities
    memory_manager.save_entity("hotel", "h456", {"name": "Other"})
    list_result = memory_manager.list_entities("hotel")
    assert len(list_result) == 2
    assert "h123" in list_result
    assert "h456" in list_result

    assert memory_manager.list_entities("nonexistent") == []

def test_run_dispatch(mock_memory_env):
    """Test the run function correctly routes actions."""
    # Remember via run
    res_rem = memory_manager.run(action="remember", key="run_key", value="run_val", category="run_cat")
    assert "✅ Memorizado: [run_cat] run_key" == res_rem

    # Recall via run
    res_rec = memory_manager.run(action="recall", key="run_key")
    assert "run_val" in res_rec

    # List via run
    for i in range(12):
        memory_manager.remember(f"k{i}", f"v{i}")

    res_list = memory_manager.run(action="list")
    assert "🧠 **Últimas memorias:**" in res_list
    lines = res_list.splitlines()
    # Header + up to 10 entries
    assert len(lines) <= 11
    assert "###" in lines[1]

def test_run_errors(mock_memory_env):
    """Test error handling in run function."""
    assert "❌ Se requiere key y value para recordar." == memory_manager.run("remember", key="only_key")
    assert "❌ Se requiere key para buscar." == memory_manager.run("recall", key="")
    assert "❌ Acción desconocida: unknown" in memory_manager.run("unknown")

    # List when empty
    assert "📭 Memoria vacía." == memory_manager.run("list")
