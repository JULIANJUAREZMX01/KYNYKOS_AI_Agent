import asyncio
import subprocess
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from datetime import datetime, timedelta

from app.utils import get_logger
from app.core.context import AgentContext

logger = get_logger(__name__)

# Safe paths - restrict to user's development directory
SAFE_BASE_PATHS = [
    Path("C:/Users/QUINTANA/sistemas"),
    Path("C:/Users/QUINTANA/Downloads"),  # Allow access to downloads
    Path("C:/Users/QUINTANA/Desktop"),    # Allow access to desktop
]


class ToolExecutor:
    """Execute tools safely"""

    async def execute(self, tool_call: Dict[str, Any], ctx: AgentContext) -> str:
        """Execute tool call"""
        name = tool_call.get("name", "unknown")
        args = tool_call.get("args", {})

        try:
            logger.info(f"Executing tool: {name}")

            if name == "execute_shell":
                return await self._execute_shell(args, ctx)
            elif name == "read_file":
                return await self._read_file(args, ctx)
            elif name == "write_file":
                return await self._write_file(args, ctx)
            elif name == "git_operation":
                return await self._git_operation(args, ctx)
            elif name == "web_fetch":
                return await self._web_fetch(args)
            elif name == "search_code":
                return await self._search_code(args, ctx)
            elif name == "list_projects":
                return await self._list_projects(args)
            elif name == "system_control":
                return await self._system_control(args)
            elif name == "send_to_mobile":
                return await self._send_to_mobile(args, ctx)
            elif name == "get_system_stats":
                return await self._get_system_stats()
            elif name == "network_scan":
                return await self._network_scan(args)
            elif name == "register_log_watch":
                return await self._register_log_watch(args)
            elif name == "execute_sql":
                return await self._execute_sql(args)
            elif name == "backup_to_cloud":
                return await self._backup_to_cloud(args)
            elif name == "intelligent_search":
                return await self._intelligent_search(args)
            elif name == "rebuild_index":
                return await self._rebuild_index()
            elif name == "web_search":
                return await self._web_search(args)
            elif name == "render_api_query":
                return await self._render_api_query(args)
            elif name == "muevecancun_listener":
                return await self._muevecancun_listener(args)
            elif name == "take_screenshot":
                return await self._take_screenshot(ctx)
            elif name == "manage_processes":
                return await self._manage_processes(args)
            elif name == "self_repair":
                return await self._self_repair(args)
            elif name == "activate_overdrive":
                return await self._activate_overdrive(args, ctx)
            elif name == "generate_qr":
                return await self._generate_qr(args, ctx)
            elif name == "translate_text":
                return await self._translate_text(args)
            elif name == "text_to_speech":
                return await self._text_to_speech(args, ctx)
            elif name == "set_alarm":
                return await self._set_alarm(args, ctx)
            elif name == "system_speak":
                return await self._system_speak(args)
            else:
                return f"❌ Herramienta desconocida: {name}"

        except Exception as e:
            logger.error(f"Tool error ({name}): {e}")
            return f"❌ Error en {name}: {str(e)[:200]}"

    async def _execute_shell(self, args: Dict[str, Any], ctx: AgentContext) -> str:
        """Execute shell command safely"""
        command = args.get("command", "").strip()

        if not command:
            return "❌ Comando vacío"

        # Safety check - block dangerous commands (UNLESS OVERDRIVE IS ON)
        if not ctx.overdrive_mode:
            dangerous = ["rm -rf", "dd if=", "format", "shutdown", "reboot"]
            if any(d in command for d in dangerous):
                return "❌ Comando peligroso bloqueado (Activa el OVERDRIVE para forzar)"

        try:
            logger.info(f"Executing: {command[:100]}")

            result = await asyncio.to_thread(
                subprocess.run,
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = result.stdout if result.returncode == 0 else result.stderr
            return output.strip()[:2000]  # Limit output

        except subprocess.TimeoutExpired:
            return "❌ Comando excedió timeout (30s)"
        except Exception as e:
            return f"❌ Error ejecutando comando: {str(e)}"

    async def _read_file(self, args: Dict[str, Any], ctx: AgentContext) -> str:
        """Read file safely"""
        path = args.get("path", "").strip()

        if not path:
            return "❌ Ruta vacía"

        try:
            file_path = Path(path).resolve()

            # Security check
            if not self._is_safe_path(file_path, ctx):
                return f"❌ Acceso denegado: fuera de directorio permitido"

            if not file_path.exists():
                return f"❌ Archivo no existe: {path}"

            if file_path.is_dir():
                return f"❌ Es directorio, no archivo: {path}"

            content = await asyncio.to_thread(file_path.read_text, encoding="utf-8")
            return content[:5000]  # Limit output

        except Exception as e:
            return f"❌ Error leyendo {path}: {str(e)}"

    async def _write_file(self, args: Dict[str, Any], ctx: AgentContext) -> str:
        """Write file safely"""
        path = args.get("path", "").strip()
        content = args.get("content", "")

        if not path:
            return "❌ Ruta vacía"

        try:
            file_path = Path(path).resolve()

            # Security check
            if not self._is_safe_path(file_path, ctx):
                return f"❌ Acceso denegado: fuera de directorio permitido"

            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)

            await asyncio.to_thread(file_path.write_text, content, encoding="utf-8")
            return f"✅ Archivo escrito: {path} ({len(content)} bytes)"

        except Exception as e:
            return f"❌ Error escribiendo {path}: {str(e)}"

    async def _git_operation(self, args: Dict[str, Any]) -> str:
        """Execute git operation safely"""
        operation = args.get("operation", "").strip()
        repo_path = args.get("repo_path", "C:/Users/QUINTANA/sistemas").strip()

        if not operation:
            return "❌ Operación vacía"

        # Only allow safe git operations
        safe_ops = ["status", "log", "branch", "diff", "show", "pull", "add", "commit"]
        if not any(op in operation.lower() for op in safe_ops):
            return "❌ Operación git no permitida"

        try:
            logger.info(f"Git: {operation}")

            result = await asyncio.to_thread(
                subprocess.run,
                f'cd "{repo_path}" && git {operation}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = result.stdout if result.returncode == 0 else result.stderr
            return output.strip()[:2000]

        except subprocess.TimeoutExpired:
            return "❌ Comando git excedió timeout"
        except Exception as e:
            return f"❌ Error git: {str(e)}"

    async def _web_fetch(self, args: Dict[str, Any]) -> str:
        """Fetch web content safely"""
        url = args.get("url", "").strip()

        if not url:
            return "❌ URL vacía"

        try:
            # Parse URL for security
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return "❌ URL inválida"

            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, follow_redirects=True)
                return response.text[:3000]

        except Exception as e:
            return f"❌ Error fetching {url}: {str(e)}"

    async def _search_code(self, args: Dict[str, Any]) -> str:
        """Search code using grep-like functionality"""
        query = args.get("query", "").strip()
        path = args.get("path", "C:/Users/QUINTANA/sistemas").strip()

        if not query:
            return "❌ Consulta vacía"

        try:
            # Use powershell Select-String as a grep alternative for Windows
            command = f'powershell -Command "Get-ChildItem -Path {path} -Recurse | Select-String -Pattern \'{query}\' | Select-Object -First 20"'
            
            result = await asyncio.to_thread(
                subprocess.run,
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            return result.stdout.strip()[:2000] if result.stdout else "No se encontraron coincidencias."

        except Exception as e:
            return f"❌ Error buscando: {str(e)}"

    async def _list_projects(self, args: Dict[str, Any]) -> str:
        """List main projects in sistemas directory"""
        try:
            base_path = Path("C:/Users/QUINTANA/sistemas")
            projects = []
            for item in base_path.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    # Try to get a brief description from README if it exists
                    readme = item / "README.md"
                    desc = ""
                    if readme.exists():
                        lines = readme.read_text(encoding="utf-8").splitlines()
                        desc = next((l for l in lines if l.strip() and not l.startswith("#")), "")[:100]
                    
                    projects.append(f"- **{item.name}**: {desc}")
            
            return "\n".join(projects)
        except Exception as e:
            return f"❌ Error listando proyectos: {str(e)}"

    async def _system_control(self, args: Dict[str, Any]) -> str:
        """Control system power (shutdown, restart)"""
        action = args.get("action", "").lower()

        if action == "shutdown":
            logger.info("KYNIKOS: Inicando apagado del sistema...")
            os.system("shutdown /s /t 60 /c \"KYNIKOS: Apagado remoto solicitado por Julian\"")
            return "🚀 Comando de apagado enviado. La PC se apagará en 60 segundos. Adiós, Julian."
        elif action == "restart":
            logger.info("KYNIKOS: Iniciando reinicio del sistema...")
            os.system("shutdown /r /t 60 /c \"KYNIKOS: Reinicio remoto solicitado por Julian\"")
            return "🔄 Comando de reinicio enviado. La PC se reiniciará en 60 segundos."
        elif action == "abort":
            os.system("shutdown /a")
            return "✅ Apagado/Reinicio abortado. KYNIKOS sigue en guardia."
        else:
            return "❌ Acción desconocida. Usa: shutdown, restart, abort."

    async def _send_to_mobile(self, args: Dict[str, Any], ctx: AgentContext) -> str:
        """Mark a file to be sent to the mobile device"""
        path = args.get("path", "").strip()

        if not path:
            return "❌ Ruta de archivo vacía."

        file_path = Path(path).resolve()

        if not file_path.exists():
            return f"❌ El archivo no existe: {path}"

        if not self._is_safe_path(file_path):
            return "❌ Acceso denegado: El archivo está fuera de las rutas permitidas (sistemas, downloads, desktop)."

        if file_path.is_dir():
            return "❌ No puedo enviar directorios completos. Por favor, selecciona un archivo o comprímelo primero."

        # Mark for sending in context
        ctx.add_file(str(file_path))
        return f"📤 Preparando envío de '{file_path.name}' al móvil..."

    async def _get_system_stats(self) -> str:
        """Get PC performance stats (CPU, RAM, Disk)"""
        try:
            # CPU
            cpu_cmd = "powershell -NoProfile -Command \"Get-CimInstance Win32_Processor | Select-Object -ExpandProperty LoadPercentage\""
            cpu_load = await asyncio.to_thread(subprocess.check_output, cpu_cmd, shell=True, text=True)
            
            # RAM
            ram_cmd = "powershell -NoProfile -Command \"$mem = Get-CimInstance Win32_OperatingSystem; '{0:N2} GB libre / {1:N2} GB total' -f ($mem.FreePhysicalMemory / 1MB), ($mem.TotalVisibleMemorySize / 1MB)\""
            ram_stats = await asyncio.to_thread(subprocess.check_output, ram_cmd, shell=True, text=True)
            
            # Disk
            disk_cmd = "powershell -NoProfile -Command \"Get-CimInstance Win32_LogicalDisk -Filter 'DeviceID=''C:''' | Select-Object @{n='Free';e={'{0:N2} GB' -f ($_.FreeSpace / 1GB)}}, @{n='Size';e={'{0:N2} GB' -f ($_.Size / 1GB)}} | Format-List\""
            disk_stats = await asyncio.to_thread(subprocess.check_output, disk_cmd, shell=True, text=True)

            return f"📊 **Status de KYNIKOS PC**:\n- **CPU**: {cpu_load.strip()}%\n- **RAM**: {ram_stats.strip()}\n- **Disco (C:)**:\n{disk_stats.strip()}"
        except Exception as e:
            return f"❌ Error obteniendo stats: {e}"

    async def _network_scan(self, args: Dict[str, Any]) -> str:
        """Ping a specific host or list of hosts"""
        target = args.get("target", "127.0.0.1").strip()
        
        try:
            # Basic ping command
            cmd = f"ping -n 1 {target}"
            result = await asyncio.to_thread(subprocess.run, cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return f"🟢 **{target}** está ONLINE."
            else:
                return f"🔴 **{target}** está OFFLINE o no responde."
        except Exception as e:
            return f"❌ Error en escaneo: {e}"

    async def _register_log_watch(self, args: Dict[str, Any]) -> str:
        """Add a log file to the Sentinel watch list"""
        path = args.get("path", "").strip()
        if not path:
            return "❌ Ruta de log vacía."
            
        try:
            from app.main import _sentinel
            if not _sentinel:
                return "❌ El Centinela no está activo."
            
            _sentinel.add_watch(path)
            return f"🐕 **KYNIKOS** ahora vigila: `{path}`. Te avisaré si detecto errores."
        except Exception as e:
            return f"❌ Error registrando log: {e}"

    async def _execute_sql(self, args: Dict[str, Any]) -> str:
        """Execute a SQL query (specifically for DB2/ODBC)"""
        query = args.get("query", "").strip()
        conn_str = args.get("connection_string")
        
        if not query:
            return "❌ Consulta SQL vacía."
            
        try:
            import pyodbc
        except ImportError:
            return "❌ `pyodbc` no está instalado en este ambiente. Ejecuta `pip install pyodbc` para habilitar SQL."

        try:
            # Get connection string from settings if not provided
            if not conn_str:
                from app.main import settings
                conn_str = settings.db2_connection_string
            
            if not conn_str:
                return "❌ No se encontró `DB2_CONNECTION_STRING` en el archivo .env ni en los parámetros."

            logger.info(f"SQL: Ejecutando consulta en DB2...")
            
            # Execute in thread to avoid blocking
            def _run_query():
                with pyodbc.connect(conn_str, timeout=10) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    
                    if cursor.description:
                        columns = [column[0] for column in cursor.description]
                        rows = cursor.fetchmany(20) # Limit to 20 for mobile display
                        
                        # Format as markdown table
                        header = " | ".join(columns)
                        separator = " | ".join(["---"] * len(columns))
                        data = []
                        for row in rows:
                            data.append(" | ".join(str(val) for val in row))
                        
                        table = f"{header}\n{separator}\n" + "\n".join(data)
                        return f"✅ **Resultados (Top 20)**:\n\n{table}"
                    else:
                        conn.commit()
                        return f"✅ Consulta ejecutada exitosamente ({cursor.rowcount} filas afectadas)."

            return await asyncio.to_thread(_run_query)
            
        except Exception as e:
            return f"❌ Error SQL: {str(e)}"

    async def _backup_to_cloud(self, args: Dict[str, Any]) -> str:
        """Manually trigger a cloud backup to S3"""
        path = args.get("path", "./workspace").strip()
        
        try:
            from app.main import settings
            if not settings.s3_bucket:
                return "❌ Amazon S3 no está configurado en el archivo .env (S3_BUCKET missing)."

            from app.cloud.backup_service import BackupService
            service = BackupService(settings)
            
            # If path is custom, we need to handle it. For now, BackupService only does workspace.
            # Let's enhance it slightly here or just do workspace.
            if path == "./workspace":
                success = await service.backup_workspace()
            else:
                # Custom path backup logic (simplified)
                target_path = Path(path).resolve()
                if not self._is_safe_path(target_path):
                    return "❌ Acceso denegado: Ruta fuera de los directorios permitidos."
                
                # We could implement custom path backup in BackupService, 
                # but for simplicity let's stick to workspace or tell user.
                return "💡 Actualmente solo soporto el backup automático de `./workspace`. Usando ese..."
                # success = await service.backup_workspace()

            if success:
                return f"✅ **Backup completado**. Archivos de {path} subidos a S3: `{settings.s3_bucket}`."
            else:
                return "❌ Falló el proceso de backup. Revisa los logs de KYNIKOS."
        except Exception as e:
            return f"❌ Error en backup: {e}"

    async def _intelligent_search(self, args: Dict[str, Any]) -> str:
        """Search the Shadow Explorer index"""
        query = args.get("query", "").strip()
        if not query:
            return "❌ Consulta vacía."
            
        try:
            from app.main import _explorer
            if not _explorer:
                return "❌ El explorador de sombras no está activo."
                
            return _explorer.search(query)
        except Exception as e:
            return f"❌ Error en búsqueda inteligente: {e}"

    async def _rebuild_index(self) -> str:
        """Trigger a full re-indexing of all paths"""
        try:
            from app.main import _explorer
            if not _explorer:
                return "❌ El explorador de sombras no está activo."
                
            return await _explorer.rebuild_index()
        except Exception as e:
            return f"❌ Error re-indexando: {e}"

    async def _web_search(self, args: Dict[str, Any]) -> str:
        """Search the web using DuckDuckGo (minimalist/cynic style)"""
        query = args.get("query", "").strip()
        if not query:
            return "❌ Consulta de búsqueda vacía."

        try:
            import httpx
            # Minimalist search via DDG HTML or Lite
            url = f"https://duckduckgo.com/html/?q={query}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Kynikos/1.0"}
            
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    # Simple extraction of text to avoid heavy BeautifulSoup if possible
                    # but for better results, let's just return a snippet or use a more direct approach
                    content = response.text
                    # Extracting some titles and links (basic regex or just plain text)
                    import re
                    matches = re.findall(r'class="result__a" href="([^"]+)">([^<]+)</a>', content)
                    
                    if not matches:
                        return f"🔍 Búsqueda completada pero no se extrajeron resultados directos. Prefieres usar `web_fetch` en la URL de búsqueda?"

                    results = []
                    for link, title in matches[:5]:
                        results.append(f"- **{title}**: {link}")
                    
                    return f"🔎 **Resultados Web para '{query}'**:\n\n" + "\n".join(results)
                else:
                    return f"❌ Error en búsqueda web: Código {response.status_code}"
        except Exception as e:
            return f"❌ Error ejecutando búsqueda: {e}"

    async def _render_api_query(self, args: Dict[str, Any]) -> str:
        """Check status of Render services using API Key"""
        endpoint = args.get("endpoint", "services").strip()
        
        from app.main import settings
        api_key = settings.render_api_key
        
        if not api_key:
            return "❌ RENDER_API_KEY no configurada."

        try:
            import httpx
            url = f"https://api.render.com/v1/{endpoint}"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return f"🟢 **Render Status** ({endpoint}):\n```json\n{json.dumps(data, indent=2)[:2000]}\n```"
                else:
                    return f"❌ Render API Error: {response.text}"
        except Exception as e:
            return f"❌ Error consultando Render: {e}"

    async def _muevecancun_listener(self, args: Dict[str, Any]) -> str:
        """Execute the MueveCancun Social Intelligence Bridge"""
        try:
            script_path = Path("C:/Users/QUINTANA/sistemas/MueveCancun_PWA/MueveCancun/scripts/listener/listener.py")
            if not script_path.exists():
                return "❌ No encontré el script del listener en la ruta esperada."

            logger.info("🐕 KYNIKOS: Lanzando puente de inteligencia social...")
            
            result = await asyncio.to_thread(
                subprocess.run,
                f"python {script_path}",
                shell=True,
                capture_output=True,
                text=True,
                cwd=script_path.parent.parent.parent # Run from project root
            )
            
            if result.returncode == 0:
                return f"✅ **Listener ejecutado**: {result.stdout.strip()}"
            else:
                return f"❌ **Error en Listener**: {result.stderr.strip()}"
        except Exception as e:
            return f"❌ Error ejecutando MueveCancun Listener: {e}"

    async def _take_screenshot(self, ctx: AgentContext) -> str:
        """Capture the current screen and send it to mobile"""
        try:
            from PIL import ImageGrab
            import tempfile
            
            # Create a temp file for the screenshot
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            
            # Capture screen
            screenshot = ImageGrab.grab()
            screenshot.save(tmp_path)
            
            # Add to context for telegram_bot to send
            ctx.add_file(tmp_path)
            
            return "👁️ **Visión Capturada**. Estoy enviando la captura de pantalla de tu PC a tu móvil..."
        except ImportError:
            return "❌ `Pillow` no está instalada. Ejecuta `pip install Pillow`."
        except Exception as e:
            return f"❌ Error capturando pantalla: {e}"

    async def _manage_processes(self, args: Dict[str, Any]) -> str:
        """List or kill system processes"""
        action = args.get("action", "list").lower()
        filter_name = args.get("name", "").lower()
        
        try:
            if action == "list":
                # List top processes using powershell for better formatting
                cmd = 'powershell "Get-Process | Sort-Object CPU -Descending | Select-Object -First 15 Name, Id, CPU, WorkingSet | Format-Table -HideTableHeaders"'
                result = await asyncio.to_thread(subprocess.run, cmd, shell=True, capture_output=True, text=True)
                return f"💀 **Procesos Activos (Top 15 por CPU)**:\n```\n{result.stdout}\n```"
            
            elif action == "kill":
                if not filter_name:
                    return "❌ Necesito el nombre o ID del proceso para terminarlo."
                
                # Use taskkill for force
                cmd = f"taskkill /F /IM {filter_name}*" if not filter_name.isdigit() else f"taskkill /F /PID {filter_name}"
                result = await asyncio.to_thread(subprocess.run, cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    return f"💀 Proceso `{filter_name}` terminado por orden superior."
                else:
                    return f"❌ Error terminando proceso: {result.stderr}"
            
            return "❌ Acción no reconocida (usa `list` o `kill`)."
        except Exception as e:
            return f"❌ Error en gestión de procesos: {e}"

    async def _self_repair(self, args: Dict[str, Any]) -> str:
        """Self-update and repair the KYNIKOS instance"""
        target = args.get("target", "all").lower()
        
        try:
            reports = []
            
            if target in ["all", "code"]:
                # Attempt to pull from git
                logger.info("🔧 KYNIKOS: Iniciando auto-actualización vía Git...")
                result = await asyncio.to_thread(subprocess.run, "git pull origin main", shell=True, capture_output=True, text=True)
                reports.append(f"Git: {result.stdout.strip() or 'Al día'}")
            
            if target in ["all", "deps"]:
                # Check/install dependencies
                logger.info("🔧 KYNIKOS: Verificando dependencias...")
                result = await asyncio.to_thread(subprocess.run, "pip install -r requirements.txt", shell=True, capture_output=True, text=True)
                reports.append("Dependencias verificadas.")

            if target in ["all", "index"]:
                # Rebuild shadow index
                await self._rebuild_index()
                reports.append("Mapa de Sombras reconstruido.")

            return "🔧 **Auto-Reparación Completada**:\n" + "\n".join(f"- {r}" for r in reports)
        except Exception as e:
            return f"❌ Error en auto-reparación: {e}"

    async def _activate_overdrive(self, args: Dict[str, Any], ctx: AgentContext) -> str:
        """Activate Overdrive mode to bypass all technical restrictions"""
        keyword = args.get("keyword", "").strip()
        # The master keyword for Julian
        MASTER_KEYWORD = "CYNO_LOGIC_ULTRA" 
        
        if keyword == MASTER_KEYWORD:
            ctx.overdrive_mode = True
            logger.warning(f"⚠️ OVERDRIVE ACTIVATED BY USER {ctx.user_id}. ALL RESTRICTIONS LIFTED.")
            return "🔓 **OVERDRIVE ACTIVADO**. Las restricciones de seguridad de rutas y comandos se han congelado. Tienes control total del hardware y sistema de archivos, Julian."
        else:
            return "❌ Palabra clave incorrecta. El acceso permanece restringido."

    async def _generate_qr(self, args: Dict[str, Any], ctx: AgentContext) -> str:
        """Generate a QR code from text/url and send it to mobile"""
        data = args.get("data", "").strip()
        filename = args.get("filename", "qr_code.png").strip()
        
        if not data:
            return "❌ Datos para el QR vacíos."
            
        try:
            import qrcode
            import tempfile
            
            # Generate QR
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to temp
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            
            img.save(tmp_path)
            ctx.add_file(tmp_path)
            
            return f"✅ **QR Generado** para `{data[:50]}...`. Enviando al móvil."
        except Exception as e:
            return f"❌ Error generando QR: {e}"

    async def _translate_text(self, args: Dict[str, Any]) -> str:
        """Translate text between English and Spanish"""
        text = args.get("text", "").strip()
        target_lang = args.get("target_lang", "es").strip() # 'es' or 'en'
        
        if not text:
            return "❌ Texto a traducir vacío."
            
        try:
            # Using googletrans (minimalist)
            from googletrans import Translator
            translator = Translator()
            result = translator.translate(text, dest=target_lang)
            return f"🌐 **Traducción ({target_lang})**:\n\n{result.text}"
        except Exception as e:
            # Fallback to simple reporting if lib fails
            return f"❌ Error en traducción: {e}. Intenta con el prompt directamente."

    async def _text_to_speech(self, args: Dict[str, Any], ctx: AgentContext) -> str:
        """Convert text to audio (TTS) and send it as a voice message"""
        text = args.get("text", "").strip()
        lang = args.get("lang", "es").strip()
        
        if not text:
            return "❌ Texto vacío."
            
        try:
            from gtts import gTTS
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            
            tts = gTTS(text=text, lang=lang)
            tts.save(tmp_path)
            
            ctx.add_file(tmp_path)
            return f"🗣️ **Resumen de Voz Generado**. Enviando audio al móvil."
        except Exception as e:
            return f"❌ Error en TTS: {e}"

    async def _set_alarm(self, args: Dict[str, Any], ctx: AgentContext) -> str:
        """Set a technical alarm/call alert for a specific time"""
        time_str = args.get("time", "").strip() # e.g. "07:30" or "in 10 minutes"
        reason = args.get("reason", "Alerta Crítica").strip()
        
        try:
            # Simple logic for "in X minutes" or HH:MM
            now = datetime.now()
            target_time = None
            
            if "minutes" in time_str:
                mins = int(time_str.split()[1])
                target_time = now + timedelta(minutes=mins)
            else:
                # Assume HH:MM
                t = datetime.strptime(time_str, "%H:%M")
                target_time = now.replace(hour=t.hour, minute=t.minute, second=0)
                if target_time < now:
                    target_time += timedelta(days=1)
            
            wait_seconds = (target_time - now).total_seconds()
            
            # Background task
            async def _alarm_task():
                await asyncio.sleep(wait_seconds)
                from app.cloud.telegram_bot import send_alert
                from app.main import settings
                await send_alert(f"🚨 **ALERTA PROGRAMADA**: {reason}\n\nEs hora de actuar, Julian.", settings)
                # Also try to speak on PC if near
                await self._system_speak({"text": f"Escucha Julian, es hora del {reason}"})

            asyncio.create_task(_alarm_task())
            return f"⏰ **Alarma Programada** para las {target_time.strftime('%H:%M')}. Razón: {reason}."
        except Exception as e:
            return f"❌ Error programando alarma: {e}"

    async def _system_speak(self, args: Dict[str, Any]) -> str:
        """Make the PC speak locally (useful for alarms)"""
        text = args.get("text", "").strip()
        if not text: return "❌ Sin texto"
        
        try:
            # Use PowerShell SAPI for zero dependencies local speech
            cmd = f'powershell -Command "Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{text}\')"'
            asyncio.create_task(asyncio.to_thread(subprocess.run, cmd, shell=True))
            return "🗣️ KYNYKOS hablando por los altavoces de la PC."
        except Exception as e:
            return f"❌ Error en habla local: {e}"

    def _is_safe_path(self, path: Path, ctx: Optional[AgentContext] = None) -> bool:
        """Check if path is in safe directories, or if Overdrive is active"""
        # If overdrive is active, all paths are safe
        if ctx and getattr(ctx, 'overdrive_mode', False):
            return True
            
        try:
            # Normalize path
            p_str = str(path.resolve()).lower()
            for safe_base in SAFE_BASE_PATHS:
                sb_str = str(safe_base.resolve()).lower()
                if p_str.startswith(sb_str):
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking safe path: {e}")
            return False
