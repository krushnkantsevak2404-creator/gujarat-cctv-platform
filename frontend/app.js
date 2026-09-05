let catalogueCameras = [];
let currentGridMode = "2x2";

document.addEventListener("DOMContentLoaded", () => {
  initClock();
  setupEventListeners();

  fetchCamerasList();
  fetchEvents();

  setInterval(fetchCamerasList, 4000);
  setInterval(fetchTelemetry, 2000);
  setInterval(fetchEvents, 3000);
});

function initClock() {
  const clockEl = document.getElementById("clock-display");
  function update() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-IN', { hour12: false }) + " IST";
    if (clockEl) clockEl.textContent = timeStr;
  }
  update();
  setInterval(update, 1000);
}

function setupEventListeners() {
  // Start Camera Stream Button (Load Management API)
  const btnStart = document.getElementById("btn-start-selected-cam");
  if (btnStart) {
    btnStart.addEventListener("click", handleStartCamera);
  }

  // Stop Camera Stream Button (Load Management API)
  const btnStop = document.getElementById("btn-stop-selected-cam");
  if (btnStop) {
    btnStop.addEventListener("click", handleStopCamera);
  }

  // Grid layout buttons
  const gridBtns = document.querySelectorAll(".btn-grid");
  gridBtns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      gridBtns.forEach(b => b.classList.remove("active"));
      const targetBtn = e.currentTarget;
      targetBtn.classList.add("active");
      currentGridMode = targetBtn.dataset.grid;
      
      const matrixGrid = document.getElementById("cctv-matrix-grid");
      if (matrixGrid) {
        matrixGrid.className = `matrix-grid grid-${currentGridMode}`;
      }
    });
  });
}

// Fetch available cameras catalogue from GET /api/cameras
async function fetchCamerasList() {
  try {
    const res = await fetch("/api/cameras");
    if (res.ok) {
      const data = await res.json();
      catalogueCameras = data.cameras || [];
      
      const modeText = document.getElementById("cctv-mode-text");
      if (modeText) modeText.textContent = (data.mode || "MOCK").toUpperCase();

      populateCameraDropdown();
      renderSidebarCatalogue();
      renderCameraMatrix();
    }
  } catch (err) {
    console.error("Error fetching cameras list:", err);
  }
}

function populateCameraDropdown() {
  const select = document.getElementById("select-camera-id");
  if (!select) return;

  const currentVal = select.value;
  select.innerHTML = catalogueCameras.map(cam => `
    <option value="${cam.id}">Cam #${cam.id} - ${cam.location} (${cam.codec || 'h264'})</option>
  `).join("");

  if (currentVal) select.value = currentVal;
}

// POST /api/cameras/{id}/start (Load Management: Open stream on demand)
async function handleStartCamera() {
  const select = document.getElementById("select-camera-id");
  const customRtspInput = document.getElementById("custom-rtsp-input");
  
  const camId = select ? select.value : "1";
  const customUrl = customRtspInput ? customRtspInput.value.trim() : null;

  try {
    const res = await fetch(`/api/cameras/${camId}/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ custom_rtsp_url: customUrl || null })
    });
    if (res.ok) {
      fetchCamerasList();
      focusCamera(camId);
    }
  } catch (err) {
    console.error("Start stream failed:", err);
  }
}

// POST /api/cameras/{id}/stop (Load Management: Close stream & release resources)
async function handleStopCamera() {
  const select = document.getElementById("select-camera-id");
  const camId = select ? select.value : "1";

  try {
    const res = await fetch(`/api/cameras/${camId}/stop`, { method: "POST" });
    if (res.ok) {
      fetchCamerasList();
    }
  } catch (err) {
    console.error("Stop stream failed:", err);
  }
}

// Render Left Sidebar Camera Items
function renderSidebarCatalogue() {
  const container = document.getElementById("camera-sidebar-list");
  const badge = document.getElementById("camera-count-badge");
  
  if (badge) badge.textContent = `${catalogueCameras.length} Feeds`;
  if (!container) return;

  container.innerHTML = catalogueCameras.map(cam => `
    <div class="camera-item" onclick="focusCamera('${cam.id}')">
      <div class="cam-info">
        <h4>Cam #${cam.id} - ${cam.location}</h4>
        <p>${cam.resolution || '1080p'} • ${cam.is_actively_consuming ? 'CONSUMING' : 'IDLE'}</p>
      </div>
      <div class="cam-meta">
        <span class="codec-tag">${cam.codec || 'h264'}</span>
        <div class="cam-status-dot ${cam.is_actively_consuming ? '' : 'reconnecting'}" 
             title="${cam.is_actively_consuming ? 'Stream Active' : 'Idle / Stopped'}"></div>
      </div>
    </div>
  `).join("");
}

// Render Camera Video Grid Matrix
function renderCameraMatrix() {
  const container = document.getElementById("cctv-matrix-grid");
  if (!container) return;

  const activeCameras = catalogueCameras.filter(c => c.is_actively_consuming);
  const displayList = activeCameras.length > 0 ? activeCameras : catalogueCameras.slice(0, 1);

  container.innerHTML = displayList.map(cam => {
    const streamUrl = `/api/stream/${cam.id}`;
    return `
      <div class="stream-card" id="card-${cam.id}">
        <div class="stream-hud-header">
          <div class="hud-title">
            <i class="fa-solid fa-video text-gold"></i>
            <span>CAM #${cam.id} - ${cam.location}</span>
          </div>
          <div class="hud-tags">
            <span class="tag-codec">${cam.codec || 'h264'}</span>
            <span class="tag-rtsp">RTSP TCP</span>
          </div>
        </div>

        <div class="stream-viewport">
          <img src="${streamUrl}" 
               alt="Cam #${cam.id} Stream" 
               onerror="handleStreamError(this, '${cam.id}')">
        </div>

        <div class="stream-hud-footer">
          <div><i class="fa-solid fa-satellite-dish"></i> ${cam.location}</div>
          <div class="hud-pts-badge" id="pts-badge-${cam.id}">
            PTS: Live Monotonic...
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function handleStreamError(imgEl, camId) {
  imgEl.onerror = null;
  imgEl.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='640' height='360' viewBox='0 0 640 360'><rect width='100%' height='100%' fill='%23080f1e'/><text x='50%' y='45%' fill='%23f1c40f' font-family='sans-serif' font-size='16' text-anchor='middle'>Stream Reconnecting (§3)...</text><text x='50%' y='55%' fill='%2364748b' font-family='sans-serif' font-size='12' text-anchor='middle'>Exponential backoff active (~2s-30s)</text></svg>";
}

// Fetch Stream Telemetries
async function fetchTelemetry() {
  try {
    const activeCams = catalogueCameras.filter(c => c.is_actively_consuming);
    for (const cam of activeCams) {
      const res = await fetch(`/api/cameras/${cam.id}/status`);
      if (res.ok) {
        const data = await res.json();
        const badge = document.getElementById(`pts-badge-${cam.id}`);
        if (badge) {
          badge.textContent = `PTS: ${Math.round(data.pts_ms || 0)}ms | Δ: ${Math.round(data.delta_pts_ms || 0)}ms`;
        }
      }
    }
  } catch (err) {}
}

// Fetch Persisted AI Events from Database
async function fetchEvents() {
  try {
    const res = await fetch("/api/events?limit=10");
    if (res.ok) {
      const data = await res.json();
      renderEvents(data.events || []);
    }
  } catch (err) {}
}

function renderEvents(events) {
  const container = document.getElementById("db-events-feed");
  if (!container) return;

  if (events.length === 0) {
    container.innerHTML = `<div style="font-size:0.75rem; color:#64748b; padding:10px;">No detection events logged yet.</div>`;
    return;
  }

  container.innerHTML = events.map(ev => `
    <div class="alert-item">
      <div class="alert-top">
        <span class="alert-type">${ev.event_type} (${ev.object_type})</span>
        <span class="alert-time">PTS ${Math.round(ev.pts_ms)}ms</span>
      </div>
      <div class="alert-details">
        Cam #${ev.camera_id} • Track #${ev.tracking_id} • Conf: ${(ev.confidence * 100).toFixed(0)}%
      </div>
    </div>
  `).join("");
}

function focusCamera(camId) {
  const matrixGrid = document.getElementById("cctv-matrix-grid");
  const gridBtns = document.querySelectorAll(".btn-grid");
  
  gridBtns.forEach(b => b.classList.remove("active"));
  const btn1x1 = document.querySelector('.btn-grid[data-grid="1x1"]');
  if (btn1x1) btn1x1.classList.add("active");

  if (matrixGrid) matrixGrid.className = "matrix-grid grid-1x1";
}
