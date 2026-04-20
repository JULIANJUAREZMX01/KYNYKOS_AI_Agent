"""Persistent memory management for Nanobot"""

import json
import aiofiles
from pathlib import Path
from typing import Any, Optional, Dict, List
from datetime import datetime

from app.utils import get_logger

logger = get_logger(__name__)


class Memory:
    """File-based memory for agent state and history"""

    def __init__(self, workspace_path: str | Path):
        self.workspace_path = Path(workspace_path)
        self.memory_file = self.workspace_path / "memory" / "MEMORY.md"
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Memory initialized: {self.memory_file}")

    async def load(self) -> Dict[str, Any]:
        """Load memory from MEMORY.md"""
        try:
            if self.memory_file.exists():
                async with aiofiles.open(self.memory_file, mode="r", encoding="utf-8") as f:
                    content = await f.read()
                return {"raw": content}
            return {}
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
            return {}

    async def save(self, content: str) -> None:
        """Save memory to MEMORY.md"""
        try:
            async with aiofiles.open(self.memory_file, mode="w", encoding="utf-8") as f:
                await f.write(content)
            logger.debug("Memory saved")
        except Exception as e:
            logger.error(f"Error saving memory: {e}")

    async def append_session(
        self, session_id: str, messages: List[Any]
    ) -> None:
        """Append session messages to JSONL log"""
        try:
            sessions_dir = self.workspace_path / "data" / "sessions"
            sessions_dir.mkdir(parents=True, exist_ok=True)

            session_file = sessions_dir / f"{session_id}.jsonl"

            async with aiofiles.open(session_file, mode="a", encoding="utf-8") as f:
                for msg in messages:
                    try:
                        # Handle Message objects
                        if hasattr(msg, 'to_dict'):
                            msg_data = msg.to_dict()
                        else:
                            msg_data = msg

                        await f.write(json.dumps(msg_data) + "\n")
                    except Exception as e:
                        logger.error(f"Error serializing message: {e}")

            logger.debug(f"Session appended: {session_id}")

        except Exception as e:
            logger.error(f"Error appending session: {e}")

    async def get_memory_context(self) -> str:
        """Get memory content for LLM context"""
        try:
            if self.memory_file.exists():
                async with aiofiles.open(self.memory_file, mode="r", encoding="utf-8") as f:
                    return await f.read()
            return ""
        except Exception as e:
            logger.error(f"Error reading memory: {e}")
            return ""
