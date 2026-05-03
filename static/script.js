/* ── Provider & Agent Definitions ─────────────────────────────── */
const PROVIDERS = {
    gemini: {
        name: "Google Gemini",
        icon: "✦",
        models: ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"],
        defaultModel: "gemini-2.5-flash",
        allowEmptyApiKey: true,
    },
    openrouter: {
        name: "OpenRouter",
        icon: "⊕",
        models: [
            "anthropic/claude-3-haiku",
            "anthropic/claude-3.5-haiku",
            "openai/gpt-4o-mini",
            "openai/gpt-4.1-nano",
            "deepseek/deepseek-chat-v3.1",
            "deepseek/deepseek-v3.2",
            "meta-llama/llama-3.1-8b-instruct",
            "mistralai/mistral-nemo",
        ],
        defaultModel: "anthropic/claude-3-haiku",
        allowEmptyApiKey: true,
    },
};

const AGENTS = [
    {
        id: 1,
        title: "Ajan 1",
        role: "Gemini · ilk taslak",
        defaultProvider: "gemini",
        lockedProvider: true,
        defaultModel: "gemini-2.5-flash",
    },
    {
        id: 2,
        title: "Ajan 2",
        role: "OpenRouter · Claude denetim",
        defaultProvider: "openrouter",
        lockedProvider: false,
        defaultModel: "anthropic/claude-3-haiku",
    },
    {
        id: 3,
        title: "Ajan 3",
        role: "OpenRouter · GPT doğrulama",
        defaultProvider: "openrouter",
        lockedProvider: false,
        defaultModel: "openai/gpt-4o-mini",
    },
    {
        id: 4,
        title: "Ajan 4",
        role: "OpenRouter · DeepSeek nihai sentez",
        defaultProvider: "openrouter",
        lockedProvider: false,
        defaultModel: "deepseek/deepseek-chat-v3.1",
    },
];

const COLORS = { 1: "#06b6d4", 2: "#8b5cf6", 3: "#f59e0b", 4: "#10b981" };

function agentConfigured(cfg) {
    if (!cfg.provider || !PROVIDERS[cfg.provider]) return false;
    if (PROVIDERS[cfg.provider].allowEmptyApiKey) return true;
    return Boolean(cfg.apiKey);
}

/* ── State ────────────────────────────────────────────────────── */
let agentConfigs = {};
let isRunning = false;

/* ── LocalStorage ─────────────────────────────────────────────── */
function saveConfigs() {
    const data = {};
    for (const [id, cfg] of Object.entries(agentConfigs)) {
        const { apiKey, ...safeCfg } = cfg;
        data[id] = safeCfg;
    }
    try { localStorage.setItem("pipeline_configs", JSON.stringify(data)); } catch {}
}

function loadConfigs() {
    try {
        const raw = localStorage.getItem("pipeline_configs");
        if (raw) return JSON.parse(raw);
    } catch {}
    return null;
}

// LocalStorage'da geçersiz/eski model isimleri varsa temizle
const VALID_MODELS = new Set(
    Object.values(PROVIDERS).flatMap((p) => p.models)
);

/* ── Init ──────────────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
    const saved = loadConfigs();
    AGENTS.forEach((agent) => {
        const s = saved && saved[agent.id];
        const provider = agent.lockedProvider ? agent.defaultProvider : (s?.provider || agent.defaultProvider || "");
        const fallbackModel = agent.defaultModel || PROVIDERS[provider]?.defaultModel || "";
        // Eğer kaydedilmiş model artık geçerli listede yoksa varsayılana düş
        const savedModel = s?.modelName;
        const modelName = (savedModel && VALID_MODELS.has(savedModel)) ? savedModel : fallbackModel;
        agentConfigs[agent.id] = {
            provider: provider,
            apiKey: "",
            modelName: modelName,
            temperature: s?.temperature ?? 0.7,
        };
    });
    renderModelCards();
});

/* ── Render Model Cards ───────────────────────────────────────── */
function renderModelCards() {
    const grid = document.getElementById("modelsGrid");
    grid.innerHTML = "";

    AGENTS.forEach((agent) => {
        const cfg = agentConfigs[agent.id];
        const isConfigured = agentConfigured(cfg);
        const provider = cfg.provider && PROVIDERS[cfg.provider] ? PROVIDERS[cfg.provider] : null;
        const card = document.createElement("div");
        card.className = `model-card${isConfigured ? " configured" : ""}${agent.lockedProvider ? " locked" : ""}`;
        card.dataset.agent = agent.id;

        const providerOptions = Object.entries(PROVIDERS)
            .map(([key, p]) => `<option value="${key}"${cfg.provider === key ? " selected" : ""}>${p.icon} ${p.name}</option>`)
            .join("");

        const modelOptions = cfg.provider && PROVIDERS[cfg.provider]
            ? PROVIDERS[cfg.provider].models
                .map((m) => `<option value="${m}"${(cfg.modelName || PROVIDERS[cfg.provider].defaultModel) === m ? " selected" : ""}>${m}</option>`)
                .join("")
            : '<option value="">Önce provider seçin</option>';

        const providerField = agent.lockedProvider
            ? `
            <div class="field">
                <label class="field-label">Provider</label>
                <div class="locked-provider">${provider?.icon || ""} ${provider?.name || "Google Gemini"}</div>
                <div class="field-help">Kilitli: bu kartta yalnızca model seçilir (aynı Gemini anahtarı).</div>
            </div>`
            : `
            <div class="field">
                <label class="field-label">Provider</label>
                <select class="field-select" id="provider_${agent.id}" onchange="onProviderChange(${agent.id})">
                    <option value="">Model sağlayıcı seçin...</option>
                    ${providerOptions}
                </select>
                <div class="field-help">Bu ajanı hangi model çalıştıracaksa kullanıcı burada seçer.</div>
            </div>`;

        card.innerHTML = `
            <div class="card-header">
                <div class="agent-badge" data-agent="${agent.id}">${agent.id}</div>
                <div class="agent-info">
                    <div class="agent-title">${agent.title}</div>
                    <div class="agent-role">${agent.role}</div>
                </div>
                <div class="status-dot${isConfigured ? " active" : ""}" title="${isConfigured ? "Yapılandırıldı" : "Yapılandırılmadı"}"></div>
            </div>

            ${providerField}

            <div class="field">
                <label class="field-label">Model</label>
                <select class="field-select" id="model_${agent.id}" onchange="onModelChange(${agent.id})">
                    ${modelOptions}
                </select>
            </div>

            <div class="field">
                <label class="field-label">API Anahtarı</label>
                <input type="password" class="field-input" id="apikey_${agent.id}"
                       placeholder="${agent.lockedProvider ? "Gemini API key — veya .env / sunucu" : (PROVIDERS[cfg.provider]?.allowEmptyApiKey ? "Opsiyonel: boşsa app.py içindeki sunucu anahtarı" : "Provider API key")}"
                       value="${cfg.apiKey}"
                       onchange="onApiKeyChange(${agent.id})">
                <div class="field-help">Boş bırakılabilir: anahtarlar önce istekteki alan, sonra .env / KEYS.txt, son olarak app.py içindeki HARDCODED_DEV_KEYS sırasıyla okunur.</div>
            </div>

            <div class="field">
                <label class="field-label">Sıcaklık (Temperature)</label>
                <div class="temp-row">
                    <input type="range" class="temp-slider" id="temp_${agent.id}"
                           min="0" max="2" step="0.1" value="${cfg.temperature}"
                           oninput="onTempChange(${agent.id})">
                    <span class="temp-value" id="tempval_${agent.id}">${cfg.temperature.toFixed(1)}</span>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

/* ── Event Handlers ───────────────────────────────────────────── */
function onProviderChange(agentId) {
    const agent = AGENTS.find((item) => item.id === agentId);
    if (agent?.lockedProvider) return;

    const sel = document.getElementById(`provider_${agentId}`);
    const prov = sel.value;
    agentConfigs[agentId].provider = prov;

    const modelSel = document.getElementById(`model_${agentId}`);
    if (prov && PROVIDERS[prov]) {
        const p = PROVIDERS[prov];
        modelSel.innerHTML = p.models.map((m) => `<option value="${m}"${m === p.defaultModel ? " selected" : ""}>${m}</option>`).join("");
        agentConfigs[agentId].modelName = p.defaultModel;
    } else {
        modelSel.innerHTML = '<option value="">Önce provider seçin</option>';
        agentConfigs[agentId].modelName = "";
    }
    updateCardStatus(agentId);
    saveConfigs();
}

function onModelChange(agentId) {
    agentConfigs[agentId].modelName = document.getElementById(`model_${agentId}`).value;
    saveConfigs();
}

function onApiKeyChange(agentId) {
    agentConfigs[agentId].apiKey = document.getElementById(`apikey_${agentId}`).value.trim();
    updateCardStatus(agentId);
    saveConfigs();
}

function onTempChange(agentId) {
    const val = parseFloat(document.getElementById(`temp_${agentId}`).value);
    agentConfigs[agentId].temperature = val;
    document.getElementById(`tempval_${agentId}`).textContent = val.toFixed(1);
    saveConfigs();
}

function updateCardStatus(agentId) {
    const cfg = agentConfigs[agentId];
    const card = document.querySelector(`.model-card[data-agent="${agentId}"]`);
    const dot = card.querySelector(".status-dot");
    const ok = agentConfigured(cfg);
    card.classList.toggle("configured", ok);
    dot.classList.toggle("active", ok);
}

/* ── Pipeline Execution ───────────────────────────────────────── */
async function runPipeline() {
    if (isRunning) return;

    const question = document.getElementById("questionInput").value.trim();
    if (!question) { alert("Lütfen bir soru girin."); return; }

    const missingAgents = AGENTS.filter((agent) => {
        const cfg = agentConfigs[agent.id];
        return !agentConfigured(cfg);
    });
    if (missingAgents.length) {
        alert(`Lütfen tüm ajanları yapılandırın: ${missingAgents.map((agent) => agent.title).join(", ")} için API key/provider eksik.`);
        return;
    }

    isRunning = true;
    const btn = document.getElementById("runBtn");
    btn.disabled = true;
    btn.innerHTML = '<span class="run-btn-icon">⏳</span> Çalışıyor...';

    const resultsSection = document.getElementById("resultsSection");
    const flow = document.getElementById("pipelineFlow");
    resultsSection.classList.add("visible");
    flow.innerHTML = "";

    const maxTokens = parseInt(document.getElementById("globalMaxTokens").value) || 2048;
    const topP = parseFloat(document.getElementById("globalTopP").value) || 0.9;

    let previousResponse = "";

    for (let i = 0; i < AGENTS.length; i++) {
        const agent = AGENTS[i];
        const cfg = agentConfigs[agent.id];

        const activeCfg = cfg;
        const providerName = activeCfg.provider ? PROVIDERS[activeCfg.provider]?.name || activeCfg.provider : "?";

        // Add arrow between cards
        if (i > 0) {
            const arrow = document.createElement("div");
            arrow.className = "pipeline-arrow";
            arrow.textContent = "↓";
            flow.appendChild(arrow);
        }

        // Create loading card
        const cardId = `result_${agent.id}`;
        const card = createResultCard(agent, providerName, null, null, true);
        card.id = cardId;
        flow.appendChild(card);

        // Scroll to card
        card.scrollIntoView({ behavior: "smooth", block: "nearest" });

        try {
            const resp = await fetch("/api/agent", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    agentNumber: agent.id,
                    question: question,
                    previousResponse: previousResponse,
                    temperature: activeCfg.temperature,
                    maxTokens: maxTokens,
                    topP: topP,
                    provider: activeCfg.provider,
                    apiKey: activeCfg.apiKey,
                    modelName: activeCfg.modelName,
                }),
            });

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({ detail: resp.statusText }));
                throw new Error(err.detail || `HTTP ${resp.status}`);
            }

            const data = await resp.json();
            previousResponse = data.text;

            // Replace loading card with result
            const newCard = createResultCard(agent, providerName, data.text, data.usage, false);
            newCard.id = cardId;
            card.replaceWith(newCard);
        } catch (err) {
            const errCard = createResultCard(agent, providerName, `HATA: ${err.message}`, null, false, true);
            errCard.id = cardId;
            card.replaceWith(errCard);
            break; // Stop pipeline on error
        }
    }

    isRunning = false;
    btn.disabled = false;
    btn.innerHTML = '<span class="run-btn-icon">▶</span> Pipeline\'ı Çalıştır';
}

/* ── Result Card Builder ──────────────────────────────────────── */
function createResultCard(agent, providerName, text, usage, loading, error = false) {
    const card = document.createElement("div");
    card.className = `result-card${loading ? " loading" : ""}${error ? " error" : ""}`;
    card.style.animationDelay = `${(agent.id - 1) * 0.1}s`;

    const color = COLORS[agent.id];
    let metaHtml = "";
    if (usage) {
        const lat = usage.latency_ms != null ? `${usage.latency_ms}ms` : "—";
        const model = usage.used_model || "—";
        const prompt = usage.prompt_tokens ?? "—";
        const compl = usage.completion_tokens ?? "—";
        metaHtml = `
            <div class="result-meta">
                <span>⏱ ${lat}</span>
                <span>📡 ${model}</span>
                <span>→ ${prompt} prompt</span>
                <span>← ${compl} completion</span>
            </div>`;
    }

    card.innerHTML = `
        <div class="result-header">
            <div class="result-agent-badge" style="background:${color}">${agent.id}</div>
            <span class="result-agent-name">${agent.title} — ${agent.role}</span>
            <span class="result-provider">${providerName}</span>
        </div>
        <div class="result-text">${loading ? "" : escapeHtml(text || "")}</div>
        ${metaHtml}
    `;
    return card;
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function clearResults() {
    document.getElementById("pipelineFlow").innerHTML = "";
    document.getElementById("resultsSection").classList.remove("visible");
}
