/**
 * AuraQuotes AI - Web Frontend Engine
 * Connects directly to Rasa REST API Webhook Channel (/webhooks/rest/webhook)
 */

// Configuration
const API_BASE = window.location.origin.includes("http") ? "" : "http://127.0.0.1:5005";
const WEBHOOK_URL = `${API_BASE}/webhooks/rest/webhook`;
const NLU_PARSE_URL = `${API_BASE}/model/parse`;
const HEALTH_URL = `${API_BASE}/health`;

// State
let senderId = localStorage.getItem("aura_sender_id");
if (!senderId) {
  senderId = "user_" + Math.random().toString(36).substring(2, 9);
  localStorage.setItem("aura_sender_id", senderId);
}

let autoTtsEnabled = false;
let favorites = JSON.parse(localStorage.getItem("aura_favorites") || "[]");
let isRecording = false;
let recognition = null;

// DOM Elements
const chatStream = document.getElementById("chatStream");
const userInput = document.getElementById("userInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
const statusBadge = document.getElementById("statusBadge");
const statusText = document.getElementById("statusText");
const themeToggleBtn = document.getElementById("themeToggleBtn");
const ttsToggleBtn = document.getElementById("ttsToggleBtn");
const clearChatBtn = document.getElementById("clearChatBtn");
const toast = document.getElementById("toast");
const favCount = document.getElementById("favCount");

// Modals
const favoritesModal = document.getElementById("favoritesModal");
const openFavoritesBtn = document.getElementById("openFavoritesBtn");
const closeFavoritesBtn = document.getElementById("closeFavoritesBtn");
const favoritesListContainer = document.getElementById("favoritesListContainer");

const nluModal = document.getElementById("nluModal");
const openNluBtn = document.getElementById("openNluBtn");
const closeNluBtn = document.getElementById("closeNluBtn");
const nluTestInput = document.getElementById("nluTestInput");
const nluTestBtn = document.getElementById("nluTestBtn");
const nluOutputContainer = document.getElementById("nluOutputContainer");

// Initialize Speech Recognition if supported
if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRec();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  recognition.onstart = () => {
    isRecording = true;
    micBtn.classList.add("recording");
    showToast("Listening... speak your mood or question");
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    userInput.value = transcript;
    sendMessage(transcript);
  };

  recognition.onerror = () => {
    isRecording = false;
    micBtn.classList.remove("recording");
  };

  recognition.onend = () => {
    isRecording = false;
    micBtn.classList.remove("recording");
  };
} else {
  micBtn.style.display = "none";
}

// Check Backend Connection Status
async function checkBackendHealth() {
  try {
    const res = await fetch(HEALTH_URL);
    if (res.ok) {
      statusBadge.style.display = "inline-flex";
      statusBadge.querySelector(".pulse-dot").style.backgroundColor = "#2ea043";
      statusText.textContent = "Online • Rasa REST API";
    } else {
      throw new Error();
    }
  } catch (err) {
    statusBadge.querySelector(".pulse-dot").style.backgroundColor = "#f85149";
    statusText.textContent = "Offline • Server Offline";
  }
}

// Send Message to Rasa REST Webhook
async function sendMessage(text) {
  const cleanText = (text || userInput.value).trim();
  if (!cleanText) return;

  // Append User message to UI
  appendMessage("user", cleanText);
  userInput.value = "";
  userInput.style.height = "auto";

  // Show Typing Indicator
  const typingIndicator = showTypingIndicator();

  try {
    const response = await fetch(WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sender: senderId,
        message: cleanText
      })
    });

    typingIndicator.remove();

    if (!response.ok) {
      throw new Error("Server error");
    }

    const messages = await response.json();
    if (!messages || messages.length === 0) {
      appendMessage("bot", "I received your message, but didn't have a response ready. Try asking for Motivation or a mood!");
      return;
    }

    for (const msg of messages) {
      if (msg.custom && msg.custom.type === "quote_card") {
        appendQuoteCard(msg.custom, msg.buttons);
      } else {
        appendMessage("bot", msg.text, msg.buttons);
      }

      // Auto Read-Aloud if enabled
      if (autoTtsEnabled && msg.text) {
        speakText(msg.text);
      }
    }
  } catch (error) {
    typingIndicator.remove();
    appendMessage("bot", "⚠️ Could not connect to the backend server. Make sure the Rasa backend (`run_app.py` or `python backend/app.py`) is running on port 5005!");
  }
}

// UI Helpers: Append Standard Message
function appendMessage(sender, text, buttons = []) {
  const row = document.createElement("div");
  row.className = `message-row ${sender}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.innerHTML = sender === "bot" ? '<i class="fa-solid fa-robot"></i>' : '<i class="fa-solid fa-user"></i>';

  const bubbleWrapper = document.createElement("div");
  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = text;
  bubbleWrapper.appendChild(bubble);

  if (buttons && buttons.length > 0) {
    const btnGroup = document.createElement("div");
    btnGroup.className = "button-group";
    buttons.forEach(btn => {
      const b = document.createElement("button");
      b.className = "reply-btn";
      b.textContent = btn.title;
      b.onclick = () => {
        const payload = btn.payload || btn.title;
        // User friendly text
        sendMessage(btn.title);
      };
      btnGroup.appendChild(b);
    });
    bubbleWrapper.appendChild(btnGroup);
  }

  row.appendChild(avatar);
  row.appendChild(bubbleWrapper);
  chatStream.appendChild(row);
  scrollToBottom();
}

// UI Helpers: Append Interactive Quote Card
function appendQuoteCard(quoteData, buttons = []) {
  const row = document.createElement("div");
  row.className = "message-row bot";

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.innerHTML = '<i class="fa-solid fa-robot"></i>';

  const cardWrapper = document.createElement("div");
  cardWrapper.style.width = "100%";

  const card = document.createElement("div");
  card.className = "quote-card";

  const isFavorited = favorites.some(f => f.id === quoteData.quote_id);

  card.innerHTML = `
    <div class="quote-badge-row">
      <span class="category-tag"><i class="fa-solid fa-tag"></i> ${quoteData.category || "Wisdom"}</span>
    </div>
    <div class="quote-text">“${escapeHtml(quoteData.quote)}”</div>
    <div class="quote-author">— ${escapeHtml(quoteData.author)}</div>
    <div class="quote-actions">
      <button class="action-pill" onclick="speakText('${escapeQuotes(quoteData.quote)} by ${escapeQuotes(quoteData.author)}')">
        <i class="fa-solid fa-volume-high"></i> Listen
      </button>
      <button class="action-pill" onclick="copyQuote('${escapeQuotes(quoteData.quote)}', '${escapeQuotes(quoteData.author)}')">
        <i class="fa-solid fa-copy"></i> Copy
      </button>
      <button class="action-pill ${isFavorited ? 'active' : ''}" onclick="toggleFavorite(this, ${quoteData.quote_id}, '${escapeQuotes(quoteData.quote)}', '${escapeQuotes(quoteData.author)}', '${escapeQuotes(quoteData.category)}')">
        <i class="fa-solid fa-bookmark"></i> ${isFavorited ? 'Saved' : 'Favorite'}
      </button>
      <button class="action-pill" onclick="sendMessage('explain this quote')">
        <i class="fa-solid fa-lightbulb"></i> Explain Meaning
      </button>
      <button class="action-pill" onclick="shareQuote('${escapeQuotes(quoteData.quote)}', '${escapeQuotes(quoteData.author)}')">
        <i class="fa-solid fa-share-nodes"></i> Share
      </button>
    </div>
  `;

  cardWrapper.appendChild(card);

  // Add satisfaction buttons below card
  if (buttons && buttons.length > 0) {
    const btnGroup = document.createElement("div");
    btnGroup.className = "button-group";
    buttons.forEach(btn => {
      const b = document.createElement("button");
      b.className = "reply-btn";
      b.textContent = btn.title;
      b.onclick = () => sendMessage(btn.title);
      btnGroup.appendChild(b);
    });
    cardWrapper.appendChild(btnGroup);
  }

  row.appendChild(avatar);
  row.appendChild(cardWrapper);
  chatStream.appendChild(row);
  scrollToBottom();
}

// Typing Indicator
function showTypingIndicator() {
  const row = document.createElement("div");
  row.className = "message-row bot typing-row";
  row.innerHTML = `
    <div class="message-avatar"><i class="fa-solid fa-robot"></i></div>
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  chatStream.appendChild(row);
  scrollToBottom();
  return row;
}

function scrollToBottom() {
  chatStream.scrollTop = chatStream.scrollHeight;
}

// Text-to-Speech (TTS)
function speakText(text) {
  if (!("speechSynthesis" in window)) {
    showToast("Speech synthesis not supported in this browser.");
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.95;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

// Copy Quote
function copyQuote(text, author) {
  const full = `“${text}” — ${author}`;
  navigator.clipboard.writeText(full).then(() => {
    showToast("Quote copied to clipboard!");
  });
}

// Share Quote
function shareQuote(text, author) {
  const full = `“${text}” — ${author}`;
  if (navigator.share) {
    navigator.share({ title: "Inspirational Quote", text: full });
  } else {
    copyQuote(text, author);
  }
}

// Favorites Management
function updateFavCount() {
  favCount.textContent = favorites.length;
}

function toggleFavorite(btn, id, quote, author, category) {
  const index = favorites.findIndex(f => f.id === id);
  if (index >= 0) {
    favorites.splice(index, 1);
    btn.classList.remove("active");
    btn.innerHTML = '<i class="fa-solid fa-bookmark"></i> Favorite';
    showToast("Removed from favorites");
  } else {
    favorites.push({ id, quote, author, category });
    btn.classList.add("active");
    btn.innerHTML = '<i class="fa-solid fa-bookmark"></i> Saved';
    showToast("Saved to favorites! ⭐");
  }
  localStorage.setItem("aura_favorites", JSON.stringify(favorites));
  updateFavCount();
}

function renderFavoritesList() {
  if (favorites.length === 0) {
    favoritesListContainer.innerHTML = '<p style="color:var(--text-muted); text-align:center; padding:20px;">No saved favorites yet. Click the bookmark button on any quote card!</p>';
    return;
  }

  favoritesListContainer.innerHTML = favorites.map(f => `
    <div class="quote-card" style="margin-bottom:14px; max-width:100%;">
      <span class="category-tag">${escapeHtml(f.category || "Quote")}</span>
      <div class="quote-text" style="font-size:1.05rem; margin-top:8px;">“${escapeHtml(f.quote)}”</div>
      <div class="quote-author">— ${escapeHtml(f.author)}</div>
      <div class="quote-actions" style="margin-top:8px; padding-top:8px;">
        <button class="action-pill" onclick="copyQuote('${escapeQuotes(f.quote)}', '${escapeQuotes(f.author)}')"><i class="fa-solid fa-copy"></i> Copy</button>
        <button class="action-pill" onclick="speakText('${escapeQuotes(f.quote)} by ${escapeQuotes(f.author)}')"><i class="fa-solid fa-volume-high"></i> Listen</button>
      </div>
    </div>
  `).join("");
}

// Toast helper
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2500);
}

// Escaping
function escapeHtml(str) {
  return (str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function escapeQuotes(str) {
  return (str || "").replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// Event Listeners
sendBtn.addEventListener("click", () => sendMessage());

userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Auto-expand textarea
userInput.addEventListener("input", function() {
  this.style.height = "auto";
  this.style.height = (this.scrollHeight) + "px";
});

// Voice Input button
micBtn.addEventListener("click", () => {
  if (!recognition) return;
  if (isRecording) {
    recognition.stop();
  } else {
    recognition.start();
  }
});

// Theme Toggle
themeToggleBtn.addEventListener("click", () => {
  document.body.classList.toggle("light-theme");
  const isLight = document.body.classList.contains("light-theme");
  themeToggleBtn.innerHTML = isLight ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
  localStorage.setItem("aura_theme", isLight ? "light" : "dark");
});

if (localStorage.getItem("aura_theme") === "light") {
  document.body.classList.add("light-theme");
  themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
}

// TTS Toggle
ttsToggleBtn.addEventListener("click", () => {
  autoTtsEnabled = !autoTtsEnabled;
  ttsToggleBtn.classList.toggle("active", autoTtsEnabled);
  showToast(autoTtsEnabled ? "Auto Read-Aloud enabled 🔊" : "Auto Read-Aloud disabled 🔇");
});

// Clear Chat
clearChatBtn.addEventListener("click", () => {
  chatStream.innerHTML = "";
  sendGreeting();
});

// Category Chips click
document.querySelectorAll(".cat-pill").forEach(pill => {
  pill.addEventListener("click", () => {
    document.querySelectorAll(".cat-pill").forEach(p => p.classList.remove("active"));
    pill.classList.add("active");
    const category = pill.getAttribute("data-category");
    if (category) {
      sendMessage(`I want ${category} quotes`);
    } else {
      sendMessage("Give me a quote");
    }
  });
});

// Mood Buttons click
document.querySelectorAll(".mood-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const mood = btn.getAttribute("data-mood");
    sendMessage(`I am feeling ${mood}`);
  });
});



// Favorites Modal
openFavoritesBtn.addEventListener("click", () => {
  renderFavoritesList();
  favoritesModal.classList.add("open");
});

closeFavoritesBtn.addEventListener("click", () => {
  favoritesModal.classList.remove("open");
});

// NLU Inspector Modal
openNluBtn.addEventListener("click", () => {
  nluModal.classList.add("open");
});

closeNluBtn.addEventListener("click", () => {
  nluModal.classList.remove("open");
});

async function runNluInspect(text) {
  nluOutputContainer.innerHTML = '<div style="color:var(--text-muted)">Analyzing NLP entities and intents...</div>';
  try {
    const res = await fetch(NLU_PARSE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text })
    });
    const data = await res.json();
    nluOutputContainer.innerHTML = `
      <div style="margin-bottom:8px;"><strong>Text:</strong> "${escapeHtml(data.text)}"</div>
      <div style="margin-bottom:8px;"><strong>Detected Intent:</strong> <span style="color:#a855f7; font-weight:bold;">${data.intent.name}</span> (${(data.intent.confidence * 100).toFixed(1)}% confidence)</div>
      <div style="margin-bottom:8px;"><strong>Extracted Entities:</strong> ${data.entities.length > 0 ? JSON.stringify(data.entities, null, 2) : 'None'}</div>
      <div style="margin-top:12px;"><strong>Intent Rankings:</strong></div>
      <ul>
        ${data.intent_ranking.map(i => `<li>${i.name}: ${(i.confidence * 100).toFixed(1)}%</li>`).join("")}
      </ul>
    `;
  } catch (err) {
    nluOutputContainer.innerHTML = '<span style="color:#f85149">Error contacting Rasa NLU endpoint.</span>';
  }
}

nluTestBtn.addEventListener("click", () => {
  const text = nluTestInput.value.trim();
  if (text) runNluInspect(text);
});

// Initial Greeting
function sendGreeting() {
  setTimeout(() => {
    appendMessage("bot", "Hello there! ✨ I am your Quotes Recommendation AI Assistant.\nTell me how you're feeling today, or choose a category below to receive personalized quotes!", [
      { title: "🌟 Inspiration", payload: "I need inspiration" },
      { title: "💪 Motivation", payload: "I need motivation" },
      { title: "🏆 Success", payload: "Give me success quotes" },
      { title: "❤️ Love", payload: "Show me love quotes" },
      { title: "😄 Humor", payload: "Make me laugh" }
    ]);
  }, 400);
}

// Initial Boot
updateFavCount();
checkBackendHealth();
sendGreeting();
setInterval(checkBackendHealth, 10000);
