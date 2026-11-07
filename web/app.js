// Dashboard Application Logic

const API_BASE = '/api';

// Tab Management
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    // Deactivate all buttons & reset aria-selected / tabindex
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('border-blue-500');
        btn.classList.add('border-transparent');
        btn.setAttribute('aria-selected', 'false');
        btn.setAttribute('tabindex', '-1');
    });
    
    // Show selected tab
    const targetTab = document.getElementById(`${tabName}-tab`);
    if (targetTab) targetTab.classList.remove('hidden');
    
    // Activate matching button
    const activeBtn = document.getElementById(`tab-${tabName}`);
    if (activeBtn) {
        activeBtn.classList.add('border-blue-500');
        activeBtn.classList.remove('border-transparent');
        activeBtn.setAttribute('aria-selected', 'true');
        activeBtn.setAttribute('tabindex', '0');
    }
    
    // Load data
    if (tabName === 'sessions') loadSessions();
    else if (tabName === 'memory') loadMemory();
    else if (tabName === 'skills') loadSkills();
    else if (tabName === 'logs') loadLogs();
}

// Load Sessions
async function loadSessions() {
    try {
        const response = await fetch(`${API_BASE}/sessions`);
        const sessions = await response.json();
        
        const list = document.getElementById('sessions-list');
        if (sessions.length === 0) {
            list.innerHTML = '<p class="text-gray-400">Sin sesiones</p>';
            return;
        }
        
        list.innerHTML = sessions.map(session => `
            <div class="bg-gray-900 p-3 rounded text-sm">
                <div class="font-mono text-blue-400">${session.session_id}</div>
                <div class="text-xs text-gray-400">${session.user_id} • ${session.channel}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading sessions:', error);
        document.getElementById('sessions-list').innerHTML = '<p class="text-red-400">Error cargando sesiones</p>';
    }
}

// Load Memory
async function loadMemory() {
    try {
        const response = await fetch(`${API_BASE}/memory`);
        const data = await response.json();
        document.getElementById('memory-text').value = data.content;
    } catch (error) {
        console.error('Error loading memory:', error);
        document.getElementById('memory-text').value = 'Error cargando memoria';
    }
}

// Save Memory
async function saveMemory() {
    const btn = document.getElementById('save-memory-btn');
    const status = document.getElementById('memory-status');
    const originalText = btn ? btn.textContent : '💾 Guardar Memoria';

    if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ Guardando...';
    }
    if (status) {
        status.textContent = '';
        status.className = 'text-sm text-gray-400';
    }

    try {
        const content = document.getElementById('memory-text').value;
        const res = await fetch(`${API_BASE}/memory`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        if (status) {
            status.textContent = '✅ Guardado correctamente';
            status.className = 'text-sm text-green-400 font-medium';
            setTimeout(() => {
                if (status.textContent === '✅ Guardado correctamente') {
                    status.textContent = '';
                }
            }, 3000);
        }
    } catch (error) {
        console.error('Error saving memory:', error);
        if (status) {
            status.textContent = '❌ Error guardando memoria';
            status.className = 'text-sm text-red-400 font-medium';
        }
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }
}

// Load Skills
async function loadSkills() {
    try {
        const response = await fetch(`${API_BASE}/skills`);
        const skills = await response.json();
        
        const list = document.getElementById('skills-list');
        if (skills.length === 0) {
            list.innerHTML = '<p class="text-gray-400">Sin skills</p>';
            return;
        }
        
        list.innerHTML = skills.map(skill => `
            <div class="bg-gray-900 p-4 rounded">
                <h3 class="font-bold text-blue-400">${skill.name}</h3>
                <pre class="text-xs text-gray-300 mt-2 overflow-x-auto">${skill.content.substring(0, 200)}...</pre>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading skills:', error);
        document.getElementById('skills-list').innerHTML = '<p class="text-red-400">Error cargando skills</p>';
    }
}

// Load Logs
async function loadLogs() {
    try {
        const response = await fetch(`${API_BASE}/logs`);
        const data = await response.json();
        
        const list = document.getElementById('logs-list');
        if (data.logs.length === 0) {
            list.innerHTML = '<p class="text-gray-400">Sin logs</p>';
            return;
        }
        
        list.innerHTML = data.logs.map(log => `<div>${log}</div>`).join('');
    } catch (error) {
        console.error('Error loading logs:', error);
        document.getElementById('logs-list').innerHTML = '<p class="text-red-400">Error cargando logs</p>';
    }
}

// Check Status
async function checkStatus() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        const status = await response.json();
        
        const statusDiv = document.getElementById('status');
        const badge = status.status === 'ok' ? 
            '<div class="status-badge status-ok">🟢 Conectado</div>' :
            '<div class="status-badge status-error">🔴 Error</div>';
        
        statusDiv.innerHTML = badge + `<p class="text-xs text-gray-400 mt-2">${status.version}</p>`;
    } catch (error) {
        console.error('Error checking status:', error);
        document.getElementById('status').innerHTML = '<div class="status-badge status-error">🔴 Desconectado</div>';
    }
}

// Keyboard navigation for WAI-ARIA tablist
function initTabNavigation() {
    const tablist = document.querySelector('[role="tablist"]');
    if (!tablist) return;

    tablist.addEventListener('keydown', (e) => {
        const tabs = Array.from(tablist.querySelectorAll('[role="tab"]'));
        const currentIndex = tabs.indexOf(document.activeElement);
        if (currentIndex === -1) return;

        let targetIndex = null;
        if (e.key === 'ArrowRight') {
            targetIndex = (currentIndex + 1) % tabs.length;
        } else if (e.key === 'ArrowLeft') {
            targetIndex = (currentIndex - 1 + tabs.length) % tabs.length;
        } else if (e.key === 'Home') {
            targetIndex = 0;
        } else if (e.key === 'End') {
            targetIndex = tabs.length - 1;
        }

        if (targetIndex !== null) {
            e.preventDefault();
            const targetTab = tabs[targetIndex];
            targetTab.focus();
            targetTab.click();
        }
    });
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    initTabNavigation();
    checkStatus();
    setInterval(checkStatus, 30000); // Check every 30 seconds
    loadSessions();
});
