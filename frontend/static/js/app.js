/* ════════════════════════════════════════════════════════════
   MediBot AI — Frontend Application JS
   Features: Auth, Chat, Voice, OCR, Analytics, Dark Mode
════════════════════════════════════════════════════════════ */

"use strict";

// ─── Constants & State ────────────────────────────────────────────────────────
const API = window.location.origin + "/api";

const state = {
  token: localStorage.getItem("medibot_token") || null,
  user: JSON.parse(localStorage.getItem("medibot_user") || "null"),
  sessionId: null,
  isTyping: false,
  voiceRecording: false,
  recognition: null,
  theme: localStorage.getItem("medibot_theme") || "dark",
};

// ─── DOM shortcuts ────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const authModal = $("authModal");
const appShell = $("appShell");

// ─── Init ─────────────────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  applyTheme(state.theme);
  if (state.token && state.user) {
    showApp();
  }
  setupTextareaAutoResize();
  setupKeyboardShortcuts();
  setupVoiceRecognition();
});

// ─── Theme ────────────────────────────────────────────────────────────────────
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  state.theme = theme;
  localStorage.setItem("medibot_theme", theme);
}
function toggleTheme() {
  applyTheme(state.theme === "dark" ? "light" : "dark");
}

// ─── Auth flows ───────────────────────────────────────────────────────────────
function switchTab(tab) {
  ["login", "register"].forEach((t) => {
    $(t + "Form").classList.toggle("hidden", t !== tab);
    document.querySelectorAll(".auth-tab").forEach((btn, i) => {
      btn.classList.toggle("active", (i === 0 && tab === "login") || (i === 1 && tab === "register"));
    });
  });
}

async function handleLogin() {
  const email = $("loginEmail").value.trim();
  const password = $("loginPassword").value;
  clearError("loginError");
  if (!email || !password) return showError("loginError", "Please fill in all fields.");
  try {
    const res = await apiPost("/auth/login", { email, password }, false);
    saveAuth(res.token, res.user);
    showApp();
  } catch (e) {
    showError("loginError", e.message || "Login failed.");
  }
}

async function handleRegister() {
  const username = $("regUsername").value.trim();
  const full_name = $("regFullname").value.trim();
  const email = $("regEmail").value.trim();
  const password = $("regPassword").value;
  clearError("registerError");
  if (!username || !email || !password) return showError("registerError", "Please fill in all required fields.");
  if (password.length < 6) return showError("registerError", "Password must be at least 6 characters.");
  try {
    const res = await apiPost("/auth/register", { username, full_name, email, password }, false);
    saveAuth(res.token, res.user);
    showApp();
  } catch (e) {
    showError("registerError", e.message || "Registration failed.");
  }
}

async function continueAsGuest() {
  try {
    const res = await apiPost("/auth/guest-token", {}, false);
    saveAuth(res.token, { username: "Guest", user_id: "guest" });
    showApp();
  } catch {
    // fallback if server is down — still let UI open
    saveAuth("guest", { username: "Guest", user_id: "guest" });
    showApp();
  }
}

function saveAuth(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem("medibot_token", token);
  localStorage.setItem("medibot_user", JSON.stringify(user));
}

function showApp() {
  authModal.classList.add("hidden");
  authModal.classList.remove("active");
  appShell.classList.remove("hidden");
  $("userLabel").textContent = state.user?.username || "User";
  loadChatHistory();
  newChat();
}

function logout() {
  state.token = null;
  state.user = null;
  state.sessionId = null;
  localStorage.removeItem("medibot_token");
  localStorage.removeItem("medibot_user");
  authModal.classList.remove("hidden");
  authModal.classList.add("active");
  appShell.classList.add("hidden");
  clearChatWindow();
}

// ─── Tab navigation ───────────────────────────────────────────────────────────
function openTab(name) {
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.add("hidden"));
  $("tab" + name.charAt(0).toUpperCase() + name.slice(1)).classList.remove("hidden");
  if (name === "analytics") loadAnalytics();
}

// ─── Chat ─────────────────────────────────────────────────────────────────────
function newChat() {
  openTab("chat");
  state.sessionId = null;
  clearChatWindow();
  $("chatTitle").textContent = "New Conversation";
  hidePredictions();
  $("emergencyBanner").classList.add("hidden");
}

function clearChatWindow() {
  const chatWindow = $("chatWindow");
  chatWindow.innerHTML = `
    <div class="welcome-screen" id="welcomeScreen">
      <div class="welcome-hero">
        <div class="hero-pulse">✚</div>
        <h1>MediBot <em>AI</em></h1>
        <p>Advanced Generative AI Healthcare Assistant</p>
      </div>
      <div class="feature-grid">
        <div class="feature-card"><span class="feat-icon">🧠</span><strong>AI Diagnosis</strong><span>40+ diseases with confidence scoring</span></div>
        <div class="feature-card"><span class="feat-icon">📚</span><strong>RAG Knowledge</strong><span>Evidence-based medical retrieval</span></div>
        <div class="feature-card"><span class="feat-icon">🚨</span><strong>Emergency Detection</strong><span>Immediate critical symptom alerts</span></div>
        <div class="feature-card"><span class="feat-icon">🗣️</span><strong>Voice Input</strong><span>Speak your symptoms naturally</span></div>
      </div>
      <p class="welcome-disclaimer">⚠️ For informational purposes only. Always consult a qualified doctor for medical advice.</p>
    </div>`;
}

function clearChat() {
  if (confirm("Clear this conversation?")) newChat();
}

async function sendMessage() {
  const input = $("userInput");
  const message = input.value.trim();
  if (!message || state.isTyping) return;

  // Remove welcome screen on first message
  const welcome = $("welcomeScreen");
  if (welcome) welcome.remove();

  appendMessage(message, "user");
  input.value = "";
  input.style.height = "auto";
  hidePredictions();

  showTyping();
  $("sendBtn").disabled = true;
  state.isTyping = true;

  // Auto-create session title from first message
  if (!state.sessionId) {
    $("chatTitle").textContent = message.slice(0, 40) + (message.length > 40 ? "…" : "");
  }

  try {
    const res = await apiPost("/chat/send", {
      message,
      session_id: state.sessionId,
      use_rag: true,
    });

    state.sessionId = res.session_id;

    hideTyping();
    appendBotMessage(res.reply, {
      provider: res.provider,
      isEmergency: res.is_emergency,
      ragUsed: res.rag_used,
      predictions: res.predictions,
    });

    if (res.is_emergency) {
      $("emergencyBanner").classList.remove("hidden");
    }

    if (res.predictions && res.predictions.length > 0) {
      showPredictions(res.predictions);
    }

    refreshHistoryItem(state.sessionId, message.slice(0, 50));

  } catch (e) {
    hideTyping();
    appendMessage("⚠️ " + (e.message || "Connection error. Please check your API configuration."), "error");
  } finally {
    $("sendBtn").disabled = false;
    state.isTyping = false;
  }
}

function quickSend(text) {
  openTab("chat");
  $("userInput").value = text;
  sendMessage();
}

// ─── Message rendering ────────────────────────────────────────────────────────
function appendMessage(text, type) {
  const chatWindow = $("chatWindow");
  const row = document.createElement("div");
  row.classList.add("msg-row", type);

  const avatar = document.createElement("div");
  avatar.classList.add("msg-avatar");
  avatar.textContent = type === "user" ? "🧑" : (type === "error" ? "⚠️" : "✚");

  const bubble = document.createElement("div");
  bubble.classList.add("msg-bubble");
  bubble.innerHTML = renderMarkdown(text);

  const meta = document.createElement("div");
  meta.classList.add("msg-meta");
  meta.innerHTML = `<span>${getTime()}</span>`;

  row.appendChild(avatar);
  const msgCol = document.createElement("div");
  msgCol.style.display = "flex"; msgCol.style.flexDirection = "column";
  if (type === "user") {
    msgCol.style.alignItems = "flex-end";
  }
  msgCol.appendChild(bubble);
  msgCol.appendChild(meta);
  row.appendChild(msgCol);

  chatWindow.appendChild(row);
  scrollToBottom();
  return row;
}

function appendBotMessage(text, opts = {}) {
  const chatWindow = $("chatWindow");
  const row = document.createElement("div");
  row.classList.add("msg-row", "bot");
  if (opts.isEmergency) row.classList.add("emergency");

  const avatar = document.createElement("div");
  avatar.classList.add("msg-avatar");
  avatar.textContent = "✚";

  const bubble = document.createElement("div");
  bubble.classList.add("msg-bubble");

  // Typewriter effect
  const finalHTML = renderMarkdown(text);
  bubble.innerHTML = "";
  const meta = document.createElement("div");
  meta.classList.add("msg-meta");
  meta.innerHTML = `
    <span>${getTime()}</span>
    ${opts.provider ? `<span class="provider-tag">${opts.provider}</span>` : ""}
    ${opts.ragUsed ? `<span class="provider-tag" style="color:var(--blue)">RAG</span>` : ""}
  `;

  const msgCol = document.createElement("div");
  msgCol.style.cssText = "display:flex;flex-direction:column;flex:1;max-width:72%";
  msgCol.appendChild(bubble);
  msgCol.appendChild(meta);

  row.appendChild(avatar);
  row.appendChild(msgCol);
  chatWindow.appendChild(row);

  // Animate text in
  typewriterHTML(bubble, finalHTML);
  scrollToBottom();
}

function typewriterHTML(el, html) {
  // Render instantly for long responses, animate for short ones
  el.innerHTML = html;
  scrollToBottom();
}

// ─── Typing indicator ─────────────────────────────────────────────────────────
function showTyping() {
  $("typingRow").classList.remove("hidden");
  scrollToBottom();
}
function hideTyping() {
  $("typingRow").classList.add("hidden");
}

// ─── Predictions strip ────────────────────────────────────────────────────────
function showPredictions(predictions) {
  const strip = $("predictionsStrip");
  const chips = $("predictionChips");
  chips.innerHTML = "";
  predictions.slice(0, 3).forEach((p) => {
    const chip = document.createElement("span");
    chip.classList.add("pred-chip", p.severity || "low");
    chip.textContent = `${p.display_name} (${p.confidence}%)`;
    chips.appendChild(chip);
  });
  strip.classList.remove("hidden");
}
function hidePredictions() {
  $("predictionsStrip").classList.add("hidden");
}

// ─── Chat history ─────────────────────────────────────────────────────────────
async function loadChatHistory() {
  try {
    const res = await apiGet("/chat/sessions");
    renderHistoryList(res.sessions || []);
  } catch { /* ignore */ }
}

function renderHistoryList(sessions) {
  const list = $("chatHistory");
  if (!sessions.length) {
    list.innerHTML = `<div class="history-empty">No conversations yet</div>`;
    return;
  }
  list.innerHTML = sessions.slice(0, 15).map((s) => `
    <div class="history-item" onclick="loadSession('${s._id}', '${escHtml(s.title || "Conversation")}')">
      ${escHtml((s.last_message || s.title || "Conversation").slice(0, 40))}
    </div>`).join("");
}

function refreshHistoryItem(sessionId, text) {
  // Add to top of list
  const list = $("chatHistory");
  const empty = list.querySelector(".history-empty");
  if (empty) empty.remove();
  const existing = list.querySelector(`[data-session="${sessionId}"]`);
  if (!existing) {
    const el = document.createElement("div");
    el.classList.add("history-item", "active");
    el.dataset.session = sessionId;
    el.textContent = text;
    el.onclick = () => loadSession(sessionId, text);
    list.prepend(el);
  }
}

async function loadSession(sessionId, title) {
  newChat();
  state.sessionId = sessionId;
  $("chatTitle").textContent = title;

  document.querySelectorAll(".history-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.session === sessionId);
  });

  try {
    const res = await apiGet(`/chat/sessions/${sessionId}/history`);
    const welcome = $("welcomeScreen");
    if (welcome) welcome.remove();

    (res.messages || []).forEach((msg) => {
      if (msg.role === "user") appendMessage(msg.content, "user");
      else appendBotMessage(msg.content, { provider: msg.provider });
    });
  } catch { /* ignore */ }
}

// ─── Analytics ────────────────────────────────────────────────────────────────
async function loadAnalytics() {
  try {
    const data = await apiGet("/analytics/dashboard");
    const s = data.stats;
    $("statChats").textContent = s.total_chats || 0;
    $("statDiagnoses").textContent = s.total_diagnoses || 0;
    $("statSessions").textContent = s.total_sessions || 0;
    $("statDiseases").textContent = s.diseases_in_kb || "40+";

    renderBarChart(data.top_diseases || []);
    renderSeverityChart(data.severity_distribution || {});
  } catch {
    ["statChats", "statDiagnoses", "statSessions"].forEach((id) => {
      $(id).textContent = "—";
    });
  }
}

function renderBarChart(diseases) {
  const container = $("topDiseases");
  if (!diseases.length) { container.innerHTML = "<p style='color:var(--text3);font-size:.85rem'>No data yet</p>"; return; }
  const max = Math.max(...diseases.map((d) => d.count), 1);
  container.innerHTML = diseases.map((d) => `
    <div class="bar-item">
      <span class="bar-label">${escHtml(d.disease)}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(d.count / max) * 100}%"></div></div>
      <span class="bar-count">${d.count}</span>
    </div>`).join("");
}

function renderSeverityChart(dist) {
  const colors = { low: "var(--accent)", medium: "var(--amber)", high: "var(--red)", emergency: "#ff0044" };
  const container = $("severityChart");
  const items = Object.entries(dist);
  if (!items.length) { container.innerHTML = "<p style='color:var(--text3);font-size:.85rem'>No data yet</p>"; return; }
  container.innerHTML = items.map(([key, val]) => `
    <div class="donut-item">
      <span class="donut-dot" style="background:${colors[key] || "var(--text3)"}"></span>
      <span style="flex:1;color:var(--text2)">${key.charAt(0).toUpperCase() + key.slice(1)}</span>
      <strong>${val}</strong>
    </div>`).join("");
}

// ─── OCR ─────────────────────────────────────────────────────────────────────
async function processOCR(event) {
  const file = event.target.files[0];
  if (!file) return;
  await uploadForOCR(file);
}

async function handleDrop(event) {
  event.preventDefault();
  const file = event.dataTransfer.files[0];
  if (file) await uploadForOCR(file);
}

async function uploadForOCR(file) {
  $("uploadZone").classList.add("hidden");
  $("ocrLoading").classList.remove("hidden");
  $("ocrResult").classList.add("hidden");

  const formData = new FormData();
  formData.append("file", file);

  const endpoint = file.type === "application/pdf" ? "/ocr/report" : "/ocr/prescription";

  try {
    const res = await fetch(API + endpoint, {
      method: "POST",
      headers: { Authorization: `Bearer ${state.token}` },
      body: formData,
    });
    const data = await res.json();

    $("ocrLoading").classList.add("hidden");
    $("ocrResult").classList.remove("hidden");
    $("ocrText").textContent = data.extracted_text || "(No text extracted)";
    $("ocrAnalysis").innerHTML = renderMarkdown(data.analysis || "Analysis unavailable.");
  } catch (e) {
    $("ocrLoading").classList.add("hidden");
    $("uploadZone").classList.remove("hidden");
    alert("OCR failed: " + e.message);
  }
}

function resetOCR() {
  $("uploadZone").classList.remove("hidden");
  $("ocrResult").classList.add("hidden");
  $("ocrFile").value = "";
}

// ─── File upload from chat input ──────────────────────────────────────────────
async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  openTab("ocr");
  await uploadForOCR(file);
}

// ─── Voice input ──────────────────────────────────────────────────────────────
function setupVoiceRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) return;

  state.recognition = new SpeechRecognition();
  state.recognition.continuous = false;
  state.recognition.interimResults = false;
  state.recognition.lang = "en-US";

  state.recognition.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    $("userInput").value = transcript;
    autoResizeTextarea($("userInput"));
  };

  state.recognition.onend = () => {
    state.voiceRecording = false;
    $("voiceBtn").classList.remove("recording");
    $("voiceBtn").title = "Voice input";
  };

  state.recognition.onerror = () => {
    state.voiceRecording = false;
    $("voiceBtn").classList.remove("recording");
  };
}

function toggleVoice() {
  if (!state.recognition) {
    alert("Voice recognition is not supported in your browser. Try Chrome or Edge.");
    return;
  }
  if (state.voiceRecording) {
    state.recognition.stop();
    state.voiceRecording = false;
    $("voiceBtn").classList.remove("recording");
  } else {
    state.recognition.start();
    state.voiceRecording = true;
    $("voiceBtn").classList.add("recording");
    $("voiceBtn").title = "Stop recording";
  }
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────
function toggleSidebar() {
  $("sidebar").classList.toggle("collapsed");
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function setupTextareaAutoResize() {
  const ta = $("userInput");
  ta.addEventListener("input", () => autoResizeTextarea(ta));
}

function autoResizeTextarea(ta) {
  ta.style.height = "auto";
  ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
}

function setupKeyboardShortcuts() {
  $("userInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
}

function scrollToBottom() {
  const cw = $("chatWindow");
  cw.scrollTo({ top: cw.scrollHeight, behavior: "smooth" });
}

function getTime() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function showError(id, msg) { const el = $(id); el.textContent = msg; el.classList.remove("hidden"); }
function clearError(id) { const el = $(id); el.textContent = ""; el.classList.add("hidden"); }

function renderMarkdown(text) {
  let html = text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // Headers
  html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
  html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");

  // Bold, italic
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

  // Code inline
  html = html.replace(/`(.+?)`/g, "<code>$1</code>");

  // HR
  html = html.replace(/^---$/gm, "<hr>");

  // Bullet lists
  html = html.replace(/^[•\-\*] (.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>[\s\S]+?<\/li>)+/g, (m) => `<ul>${m}</ul>`);

  // Emoji lines → keep as-is, just line break
  html = html.replace(/\n/g, "<br>");

  return html;
}

// ─── API helpers ──────────────────────────────────────────────────────────────
async function apiPost(path, body, auth = true) {
  const headers = { "Content-Type": "application/json" };
  if (auth && state.token) headers["Authorization"] = `Bearer ${state.token}`;

  const res = await fetch(API + path, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || data.message || "Request failed");
  return data;
}

async function apiGet(path) {
  const headers = {};
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;
  const res = await fetch(API + path, { headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}
