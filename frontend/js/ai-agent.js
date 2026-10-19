/* Additive AI analysis + assistant UI. Does not replace dashboard.js. */
(function () {
    "use strict";
    const byId = (id) => document.getElementById(id);
    const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
    let loadedFiles = [];

    async function getJson(url, options) {
        const response = await fetch(url, { credentials: "same-origin", ...(options || {}) });
        let data;
        try { data = await response.json(); } catch (_) { data = {}; }
        if (!response.ok || data.success === false) throw new Error(data.message || `Request failed (${response.status})`);
        return data;
    }

    function fillSelect(select, files, defaultLabel) {
        if (!select) return;
        const previous = select.value;
        select.innerHTML = `<option value="">${esc(defaultLabel)}</option>` + files.map((file) => `<option value="${Number(file.id)}">${esc(file.name)}</option>`).join("");
        if (files.some((file) => String(file.id) === previous)) select.value = previous;
    }

    async function loadAiFiles() {
        const analysisSelect = byId("aiDatasetSelect");
        const agentSelect = byId("aiAgentDataset");
        try {
            const data = await getJson("/api/files/list");
            loadedFiles = Array.isArray(data.files) ? data.files : [];
            fillSelect(analysisSelect, loadedFiles, "Select a dataset");
            fillSelect(agentSelect, loadedFiles, "No dataset selected");
        } catch (error) {
            if (analysisSelect) analysisSelect.innerHTML = '<option value="">Log in to load datasets</option>';
            if (agentSelect) agentSelect.innerHTML = '<option value="">No dataset selected</option>';
            const status = byId("aiAnalysisStatus");
            if (status) status.textContent = error.message;
        }
    }

    async function runAnalysis() {
        const select = byId("aiDatasetSelect");
        const status = byId("aiAnalysisStatus");
        const output = byId("aiAnalysisOutput");
        if (!select || !select.value) { if (status) status.textContent = "Please select a dataset first."; return; }
        const button = byId("runAiAnalysis");
        if (button) button.disabled = true;
        if (status) status.textContent = "Analyzing dataset statistics...";
        if (output) output.textContent = "";
        try {
            const data = await getJson(`/api/ai/analysis/${encodeURIComponent(select.value)}`);
            const summary = data.summary || {};
            const insights = Array.isArray(data.insights) ? data.insights : [];
            if (output) output.innerHTML = `<p><strong>${esc(summary.filename || "Dataset")}</strong> · ${Number(summary.rows || 0).toLocaleString()} rows · ${Number(summary.columns || 0)} columns</p><p>${esc(data.ai_analysis || "No analysis was returned.")}</p><h3>Key findings</h3><ul class="ai-insight-list">${insights.map((item) => `<li>${esc(item)}</li>`).join("")}</ul><p class="ai-mode-note">${esc(data.message || "")}</p>`;
            if (status) status.textContent = "Analysis complete.";
        } catch (error) { if (status) status.textContent = error.message; }
        finally { if (button) button.disabled = false; }
    }

    async function askAgent(event) {
        event.preventDefault();
        const messageEl = byId("aiAgentMessage");
        const status = byId("aiAgentStatus");
        const output = byId("aiAgentAnswer");
        const button = byId("aiAgentSend");
        const message = messageEl ? messageEl.value.trim() : "";
        if (!message) { if (status) status.textContent = "Enter a question first."; return; }
        if (button) button.disabled = true;
        if (status) status.textContent = "The AI agent is preparing an answer...";
        if (output) output.textContent = "";
        const selectedFile = byId("aiAgentDataset");
        try {
            const payload = { message };
            if (selectedFile && selectedFile.value) payload.file_id = Number(selectedFile.value);
            const data = await getJson("/api/ai/agent", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
            if (output) output.textContent = data.answer || "No answer was returned.";
            if (status) status.textContent = data.mode === "openai" ? "AI agent response generated." : "Built-in assistant response (configure OPENAI_API_KEY for conversational AI).";
        } catch (error) { if (status) status.textContent = error.message; }
        finally { if (button) button.disabled = false; }
    }

    document.addEventListener("DOMContentLoaded", function () {
        if (byId("runAiAnalysis")) byId("runAiAnalysis").addEventListener("click", runAnalysis);
        if (byId("aiAgentForm")) byId("aiAgentForm").addEventListener("submit", askAgent);
        loadAiFiles();
        // Refresh the selectors after uploads made by the existing dashboard code.
        const fileList = byId("filesList");
        if (fileList && typeof MutationObserver !== "undefined") {
            new MutationObserver(() => loadAiFiles()).observe(fileList, { childList: true, subtree: true });
        }
        const uploadForm = byId("uploadForm") || byId("dashboard-upload-form");
        if (uploadForm) uploadForm.addEventListener("submit", () => window.setTimeout(loadAiFiles, 1500));
    });
})();
