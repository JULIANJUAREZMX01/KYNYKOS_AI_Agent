import asyncio
import os
from pathlib import Path
from typing import List, Dict
from app.config import Settings
from app.utils import get_logger

logger = get_logger(__name__)

class LogSentinel:
    """Proactive log monitor for KYNIKOS"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.watch_list: Dict[str, int] = {} # Path: last_position
        self.is_running = False
        
        # Default logs to watch
        self.add_watch("logs/kynikos.log")

    def add_watch(self, file_path: str):
        """Add a log file to the monitor list"""
        path = Path(file_path).resolve()
        if path.exists():
            # Start from the end of the file
            self.watch_list[str(path)] = path.stat().st_size
            logger.info(f"🐕 Centinela vigilando: {file_path}")
        else:
            # If it doesn't exist, create it or wait for it
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            self.watch_list[str(path)] = 0
            logger.info(f"🐕 Centinela esperando archivo: {file_path}")

    async def run(self):
        """Main loop for log monitoring"""
        self.is_running = True
        from app.cloud.telegram_bot import send_alert
        from app.cloud.whatsapp_bridge import send_whatsapp_alert
        
        while self.is_running:
            for path_str, last_pos in list(self.watch_list.items()):
                try:
                    path = Path(path_str)
                    if not path.exists():
                        continue
                        
                    current_size = path.stat().st_size
                    
                    if current_size < last_pos:
                        # File was truncated/rotated
                        self.watch_list[path_str] = 0
                        continue
                        
                    if current_size > last_pos:
                        # New data!
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            f.seek(last_pos)
                            new_lines = f.readlines()
                            
                        self.watch_list[path_str] = current_size
                        
                        # Analyze lines
                        for line in new_lines:
                            if any(trigger in line.upper() for trigger in ["ERROR", "CRITICAL", "EXCEPTION", "FAILED"]):
                                # Send alert to all configured channels
                                message = f"Fallo detectado en {path.name}:\n`{line.strip()[:200]}`"
                                await send_alert(message, self.settings)
                                await send_whatsapp_alert(message, self.settings)
                                
                except Exception as e:
                    # Don't use logger.error here as it might trigger a loop if watching kynikos.log
                    print(f"Centinela Error: {e}")
                    
            await asyncio.sleep(5) # Check every 5 seconds

    def stop(self):
        self.is_running = False
