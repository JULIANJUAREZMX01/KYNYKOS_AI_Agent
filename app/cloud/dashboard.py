"""Dashboard API routes for Nanobot"""

from fastapi import APIRouter
from pathlib import Path
import json
import os
from app.utils import get_logger

logger = get_logger(__name__)


def _read_last_line_from_file(file_path: Path, buffer_size: int = 4096) -> str:
    """
    ⚡ Bolt Optimization: Read only the last non-empty line of a file by seeking backwards
    from the end of the file in chunks, instead of reading the entire file into memory
    and splitting strings. Correctly handles lines larger than buffer_size by ensuring
    a preceding newline is found or the beginning of the file is reached.
    """
    with open(file_path, "rb") as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        if file_size == 0:
            return ""

        remaining = file_size
        buffer = b""
        while remaining > 0:
            read_size = min(buffer_size, remaining)
            remaining -= read_size
            f.seek(remaining)
            chunk = f.read(read_size)
            buffer = chunk + buffer

            # Strip trailing newlines/spaces from the end of the buffer
            # to avoid false empty segments at EOF
            trimmed = buffer.rstrip(b"\r\n")
            if not trimmed:
                continue

            last_newline_idx = trimmed.rfind(b"\n")
            if last_newline_idx != -1:
                # Preceding newline found: the line after it is complete
                last_line = trimmed[last_newline_idx + 1:].strip()
                if last_line:
                    return last_line.decode("utf-8", errors="replace")
            elif remaining == 0:
                # Reached the start of the file without preceding newline
                last_line = trimmed.strip()
                if last_line:
                    return last_line.decode("utf-8", errors="replace")

    return ""


def create_dashboard_routes() -> APIRouter:
    """Create dashboard API routes"""
    router = APIRouter()
    
    @router.get("/sessions")
    async def get_sessions():
        """Get all sessions"""
        # Use plural and specific directory
        sessions_dir = Path("./data/sessions")
        if not sessions_dir.exists():
            return []
        
        sessions = []
        # Check for both .json and .jsonl
        for session_file in list(sessions_dir.glob("*.json")) + list(sessions_dir.glob("*.jsonl")):
            try:
                if session_file.suffix == ".jsonl":
                    # ⚡ Bolt Optimization: Read only the last line instead of slurp + split
                    last_line = _read_last_line_from_file(session_file)
                    if not last_line:
                        continue
                    data = json.loads(last_line)
                else:
                    content = session_file.read_text(encoding="utf-8")
                    data = json.loads(content)
                
                # Add file info
                data["session_id"] = session_file.stem
                data["last_modified"] = os.path.getmtime(session_file)
                sessions.append(data)
            except Exception as e:
                logger.error(f"Error reading session {session_file}: {e}")
                continue
        
        # Sort by last modified
        sessions.sort(key=lambda x: x.get("last_modified", 0), reverse=True)
        return sessions[:50]
    
    @router.get("/memory")
    async def get_memory():
        """Get MEMORY.md content"""
        memory_file = Path("./workspace/memory/MEMORY.md")
        if memory_file.exists():
            return {"content": memory_file.read_text(encoding="utf-8")}
        return {"content": "# Memory not found\n\nThe memory file hasn't been created yet."}
    
    @router.post("/memory")
    async def update_memory(data: dict):
        """Update MEMORY.md content"""
        content = data.get("content", "")
        memory_file = Path("./workspace/memory/MEMORY.md")
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        memory_file.write_text(content, encoding="utf-8")
        logger.info("Memory updated via dashboard")
        return {"success": True}
    
    @router.get("/skills")
    async def get_skills():
        """List available skills"""
        skills_dir = Path("./workspace/skills")
        if not skills_dir.exists():
            return []
        
        skills = []
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    skills.append({
                        "name": skill_dir.name,
                        "content": skill_md.read_text(encoding="utf-8")
                    })
        
        return skills
    
    @router.get("/logs")
    async def get_logs(limit: int = 50):
        """Get recent logs from standard logger (simple version)"""
        # This is a placeholder for a real log file reader
        # Since we use loguru/standard logger, we would need to read from a file
        return {"logs": ["Logs system ready", "Checking for activity..."], "message": "Real-time logs can be seen in Render Dashboard"}
    
    return router
