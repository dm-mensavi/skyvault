/**
 * SkyVault base utilities: Google Drive theme, global context menus, modals, preview overlays, trash actions, toasts
 */
const SkyVault = {
  init() {
    this.applySavedTheme();
    this.bindThemeToggle();
    this.bindGlobalContextMenu();
  },

  applySavedTheme() {
    const saved = localStorage.getItem("skyvault-theme") || "light";
    document.documentElement.setAttribute("data-theme", saved);
  },

  bindThemeToggle() {
    const btn = document.getElementById("theme-toggle");
    if (!btn) return;
    btn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("skyvault-theme", next);
      this.showToast(`Switched to ${next} mode`, "info");
    });
  },

  toggleSidebar() {
    document.getElementById("sidebar")?.classList.toggle("collapsed");
    document.querySelector(".main-panel")?.classList.toggle("sidebar-collapsed");
  },

  getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || "";
  },

  showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("show"));
    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  // Custom Modal confirm replace browser confirm()
  confirm({ title = "Confirm Action", message, confirmLabel = "Confirm", danger = false }) {
    return new Promise((resolve) => {
      const modal = document.getElementById("confirm-modal");
      const msgEl = document.getElementById("confirm-modal-message");
      const titleEl = document.getElementById("confirm-modal-title");
      const okBtn = document.getElementById("confirm-modal-ok");
      if (!modal || !msgEl || !okBtn) {
        resolve(window.confirm(message));
        return;
      }

      titleEl.textContent = title;
      msgEl.textContent = message;
      okBtn.textContent = confirmLabel;
      okBtn.className = danger ? "btn btn-danger" : "btn btn-primary";

      const cleanup = (result) => {
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
        okBtn.onclick = null;
        resolve(result);
      };

      okBtn.onclick = () => cleanup(true);
      modal.classList.add("open");
      modal.setAttribute("aria-hidden", "false");
      modal._dismissResolve = () => cleanup(false);
    });
  },

  closeConfirmModal() {
    const modal = document.getElementById("confirm-modal");
    if (modal && modal._dismissResolve) {
      modal._dismissResolve();
    } else if (modal) {
      modal.classList.remove("open");
    }
  },

  escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  },

  // In-App File Preview Overlay Modal
  openPreviewModal(fileId) {
    const modal = document.getElementById("preview-modal");
    const title = document.getElementById("preview-title");
    const icon = document.getElementById("preview-icon");
    const body = document.getElementById("preview-body");
    const aiContent = document.getElementById("preview-ai-content");

    if (!modal) return;

    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    body.innerHTML = '<div class="spinner-container"><span class="material-icons spinner">sync</span> Loading preview...</div>';

    fetch(`/vault/preview-file/${fileId}/`)
      .then((res) => res.json())
      .then((data) => {
        if (!data.success) {
          body.innerHTML = `<p class="error-msg">Unable to load preview.</p>`;
          return;
        }

        title.textContent = data.name;
        const ext = data.extension;

        if (["jpg", "jpeg", "png", "gif", "webp", "svg"].includes(ext)) {
          icon.textContent = "image";
          body.innerHTML = `<div class="image-preview-wrapper"><img src="${data.url}" alt="${data.name}" class="preview-img" style="max-width:100%;max-height:60vh;object-fit:contain;display:block;margin:0 auto;"></div>`;
        } else if (ext === "pdf") {
          icon.textContent = "picture_as_pdf";
          body.innerHTML = `
            <div class="pdf-preview-container" style="width:100%;height:60vh;border-radius:8px;overflow:hidden;">
              <object data="${data.url}" type="application/pdf" style="width:100%;height:100%;">
                <iframe src="${data.url}" style="width:100%;height:100%;border:none;">
                  <div class="download-preview-box">
                    <span class="material-icons big-icon">picture_as_pdf</span>
                    <p>PDF inline preview not supported directly by browser.</p>
                    <a href="${data.url}" target="_blank" class="btn btn-primary">Open PDF in New Tab</a>
                  </div>
                </iframe>
              </object>
            </div>`;
        } else if (["txt", "md", "json", "py", "js", "html", "css"].includes(ext)) {
          icon.textContent = "description";
          body.innerHTML = `<pre class="preview-code" style="max-height:60vh;overflow:auto;padding:16px;background:var(--bg-primary);border-radius:8px;font-family:monospace;white-space:pre-wrap;word-break:break-word;">${this.escapeHtml(data.text_content || "")}</pre>`;
        } else {
          icon.textContent = "insert_drive_file";
          body.innerHTML = `
            <div class="download-preview-box">
              <span class="material-icons big-icon">insert_drive_file</span>
              <p>No inline preview available for .${ext} files.</p>
              <a href="${data.url}" download="${data.name}" class="btn btn-primary">Download File</a>
            </div>`;
        }

        // Render AI analysis slot based on processing status
        aiContent.innerHTML = this.renderAiAnalysis(data.ai_analysis);
      })
      .catch((err) => {
        console.error("Preview error:", err);
        body.innerHTML = `<p class="error-msg">Error loading file preview.</p>`;
      });
  },

  closePreviewModal() {
    const modal = document.getElementById("preview-modal");
    if (modal) {
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
    }
  },

  // Renders the AI analysis slot based on FileAnalysis status (Phase 1).
  renderAiAnalysis(ai) {
    if (!ai) {
      return `<p class="ai-placeholder-text"><span class="material-icons">info</span> AI analysis is not available for this file type.</p>`;
    }

    const status = ai.status || "pending";

    if (status === "done") {
      const chips = (ai.tags || [])
        .map((t) => `<span class="chip">#${this.escapeHtml(t)}</span>`)
        .join(" ");
      const folder = ai.suggested_folder
        ? `<p class="ai-suggested-folder"><span class="material-icons">folder_open</span> Suggested folder: <strong>${this.escapeHtml(ai.suggested_folder)}</strong></p>`
        : "";
      return `
        <p><strong>Summary:</strong> ${this.escapeHtml(ai.summary || "")}</p>
        <div class="tag-chips">${chips}</div>
        ${folder}`;
    }

    if (status === "pending" || status === "processing") {
      return `<p class="ai-placeholder-text"><span class="material-icons spinner">sync</span> Analyzing document… tags and summary will appear here shortly.</p>`;
    }

    if (status === "failed") {
      return `<p class="ai-placeholder-text error-msg"><span class="material-icons">error_outline</span> AI analysis failed for this file.</p>`;
    }

    if (status === "skipped") {
      return `<p class="ai-placeholder-text"><span class="material-icons">block</span> AI analysis was skipped for this file type.</p>`;
    }

    return `<p class="ai-placeholder-text"><span class="material-icons">info</span> AI analysis is not available.</p>`;
  },

  openAiAssistant(event) {
    if (event) event.preventDefault();
    this.openRagModal();
  },

  openRagModal() {
    const modal = document.getElementById("rag-chat-modal");
    if (modal) {
      modal.classList.add("open");
      modal.setAttribute("aria-hidden", "false");
      const input = document.getElementById("rag-input");
      if (input) input.focus();
    }
  },

  closeRagModal() {
    const modal = document.getElementById("rag-chat-modal");
    if (modal) {
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
    }
  },

  submitRagQuery() {
    const input = document.getElementById("rag-input");
    const chatBody = document.getElementById("rag-chat-body");
    if (!input || !chatBody) return;

    // One question at a time. Without this, a second submit during the (often
    // multi-second) first request leaves an orphaned loading bubble that no
    // response ever clears.
    if (this._ragInFlight) return;

    const query = input.value.trim();
    if (!query) return;

    // Append user question message
    const userMsg = document.createElement("div");
    userMsg.className = "rag-message user-msg";
    userMsg.style.cssText = "display:flex; justify-content:flex-end;";
    userMsg.innerHTML = `<div style="background:var(--primary-color, #1a73e8); color:#fff; padding:10px 16px; border-radius:18px; max-width:80%; font-size:14px;">${this.escapeHtml(query)}</div>`;
    chatBody.appendChild(userMsg);

    input.value = "";
    chatBody.scrollTop = chatBody.scrollHeight;

    this._setRagBusy(true);

    // Append loading spinner placeholder
    const loadingMsg = document.createElement("div");
    loadingMsg.className = "rag-message ai-msg loading-msg";
    loadingMsg.style.cssText = "display:flex; gap:12px; background:var(--bg-hover, #f8f9fa); padding:12px 16px; border-radius:8px;";
    loadingMsg.innerHTML = `<span class="material-icons spinner" style="color:var(--primary-color,#1a73e8);">sync</span><p style="margin:0; font-size:14px; color:var(--text-muted);">Searching vector embeddings & generating answer...</p>`;
    chatBody.appendChild(loadingMsg);
    chatBody.scrollTop = chatBody.scrollHeight;

    fetch("/vault/ask/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": this.getCsrfToken(),
      },
      body: JSON.stringify({ query: query }),
    })
      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
      .then(({ ok, data }) => {
        // Non-2xx (e.g. the 503 retrieval-unavailable path) carries an `error`
        // string, not an answer — render it as an error, not as a real reply.
        if (!ok || data.error) {
          this._appendRagError(chatBody, data.error || "Failed to get AI answer. Please try again.");
          return;
        }

        const aiMsg = document.createElement("div");
        aiMsg.className = "rag-message ai-msg";
        aiMsg.style.cssText = "display:flex; gap:12px; background:var(--bg-hover, #f8f9fa); padding:14px 16px; border-radius:8px;";

        let sourcesHtml = "";
        if (data.sources && data.sources.length > 0) {
          sourcesHtml = `<div style="margin-top:12px; padding-top:10px; border-top:1px solid var(--border-color, #dadce0); font-size:12px; color:var(--text-secondary);">
            <strong>Cited Sources:</strong>
            <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:6px;">
              ${data.sources.map(s => `<span onclick="SkyVault.openPreviewModal(${s.id})" style="cursor:pointer; background:var(--primary-light, #e8f0fe); color:var(--primary-color, #1a73e8); padding:3px 8px; border-radius:12px; font-weight:500;"><span class="material-icons" style="font-size:12px; vertical-align:middle;">description</span> ${this.escapeHtml(s.name)}</span>`).join("")}
            </div>
          </div>`;
        }

        aiMsg.innerHTML = `
          <span class="material-icons" style="color:var(--primary-color, #1a73e8);">auto_awesome</span>
          <div style="flex:1;">
            <p style="margin:0; font-size:14px; line-height:1.5; white-space:pre-wrap;">${this.escapeHtml(data.answer || "")}</p>
            ${sourcesHtml}
          </div>`;

        chatBody.appendChild(aiMsg);
        chatBody.scrollTop = chatBody.scrollHeight;
      })
      .catch((err) => {
        console.error("RAG Error:", err);
        this._appendRagError(chatBody, "Failed to get AI answer. Please try again.");
      })
      .finally(() => {
        // Sweep by class, not by captured node: idempotent, clears any orphan
        // left by an earlier request, and .remove() never throws.
        chatBody.querySelectorAll(".loading-msg").forEach((n) => n.remove());
        chatBody.scrollTop = chatBody.scrollHeight;
        this._setRagBusy(false);
      });
  },

  _setRagBusy(busy) {
    this._ragInFlight = busy;
    const input = document.getElementById("rag-input");
    const btn = document.querySelector('#rag-chat-modal .rag-chat-input-row button');
    if (input) input.disabled = busy;
    if (btn) {
      btn.disabled = busy;
      btn.style.opacity = busy ? "0.6" : "";
      btn.style.cursor = busy ? "not-allowed" : "";
    }
    if (!busy && input) input.focus();
  },

  _appendRagError(chatBody, message) {
    const errorMsg = document.createElement("div");
    errorMsg.className = "rag-message ai-msg error-msg";
    errorMsg.style.cssText = "display:flex; gap:12px; background:#fce8e6; padding:12px 16px; border-radius:8px; color:#c5221f;";
    errorMsg.innerHTML = `<span class="material-icons">error_outline</span><p style="margin:0; font-size:14px;">${this.escapeHtml(message)}</p>`;
    chatBody.appendChild(errorMsg);
    chatBody.scrollTop = chatBody.scrollHeight;
  },


  // Global Context Menu binding covering entire page background
  bindGlobalContextMenu() {
    const mainPanel = document.querySelector(".main-panel");
    if (!mainPanel) return;

    mainPanel.addEventListener("contextmenu", (e) => {
      // If clicking inside a card with specific custom menu, defer to item menu
      if (e.target.closest(".drive-card") || e.target.closest(".file-item")) {
        return;
      }
      e.preventDefault();
      this.showGlobalContextMenu(e.clientX, e.clientY);
    });

    document.addEventListener("click", () => this.hideContextMenus());
  },

  showGlobalContextMenu(x, y) {
    this.hideContextMenus();
    let menu = document.getElementById("global-context-menu");
    const hasClipboard = !!sessionStorage.getItem("skyvault-clipboard");

    if (!menu) {
      menu = document.createElement("div");
      menu.id = "global-context-menu";
      menu.className = "context-menu";
      document.body.appendChild(menu);
    }

    menu.innerHTML = `
      <div class="menu-item" onclick="location.reload()"><span class="material-icons">refresh</span> Refresh Page</div>
      <div class="menu-item" onclick="SkyVault.triggerUpload()"><span class="material-icons">upload_file</span> Upload File</div>
      <div class="menu-item" onclick="SkyVault.triggerCreateFolder()"><span class="material-icons">create_new_folder</span> New Folder</div>
      ${hasClipboard ? `<div class="menu-item" onclick="SkyVaultDrive ? SkyVaultDrive.pasteItem() : null()"><span class="material-icons">content_paste</span> Paste</div>` : ''}
    `;

    menu.style.left = `${x}px`;
    menu.style.top = `${y}px`;
    menu.classList.add("open");
  },

  showTrashContextMenu(e, id, type, name) {
    e.preventDefault();
    e.stopPropagation();
    this.hideContextMenus();

    let menu = document.getElementById("trash-context-menu");
    if (!menu) {
      menu = document.createElement("div");
      menu.id = "trash-context-menu";
      menu.className = "context-menu";
      document.body.appendChild(menu);
    }

    menu.innerHTML = `
      <div class="menu-item" onclick="SkyVault.handleRestore('${id}', '${type}', '${name}')"><span class="material-icons">restore</span> Restore</div>
      <div class="menu-item danger" onclick="SkyVault.handlePermanentDelete('${id}', '${type}', '${name}')"><span class="material-icons">delete_forever</span> Delete Permanently</div>
    `;

    menu.style.left = `${e.clientX}px`;
    menu.style.top = `${e.clientY}px`;
    menu.classList.add("open");
  },

  hideContextMenus() {
    document.querySelectorAll(".context-menu").forEach((m) => m.classList.remove("open"));
  },

  triggerUpload() {
    const uploadInput = document.querySelector('input[type="file"]');
    if (uploadInput) uploadInput.click();
    else this.showToast("Navigate to My Drive or a Folder to upload files.", "info");
  },

  triggerCreateFolder() {
    const modalBtn = document.getElementById("create-folder-btn");
    if (modalBtn) modalBtn.click();
    else this.showToast("Navigate to My Drive to create new folders.", "info");
  },

  // Trash actions using custom UI modals
  async handleRestore(id, type, name) {
    this.hideContextMenus();
    const confirmed = await this.confirm({
      title: "Restore Item",
      message: `Are you sure you want to restore "${name}" back to your drive?`,
      confirmLabel: "Restore",
      danger: false,
    });

    if (!confirmed) return;

    try {
      const res = await fetch(`/vault/restore/${type}/${id}/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": this.getCsrfToken(),
          "Content-Type": "application/json",
        },
      });
      const data = await res.json();
      if (data.success) {
        this.showToast(`${type.charAt(0).toUpperCase() + type.slice(1)} restored successfully.`, "success");
        setTimeout(() => location.reload(), 600);
      } else {
        this.showToast(data.error || "Error restoring item.", "error");
      }
    } catch (err) {
      console.error(err);
      this.showToast("Network error restoring item.", "error");
    }
  },

  async handlePermanentDelete(id, type, name) {
    this.hideContextMenus();
    const confirmed = await this.confirm({
      title: "Delete Permanently",
      message: `Are you sure you want to permanently delete "${name}"? This action CANNOT be undone.`,
      confirmLabel: "Delete Permanently",
      danger: true,
    });

    if (!confirmed) return;

    try {
      const res = await fetch(`/vault/delete-permanent/${type}/${id}/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": this.getCsrfToken(),
          "Content-Type": "application/json",
        },
      });
      const data = await res.json();
      if (data.success) {
        this.showToast(`${type.charAt(0).toUpperCase() + type.slice(1)} permanently deleted.`, "success");
        setTimeout(() => location.reload(), 600);
      } else {
        this.showToast(data.error || "Error deleting item.", "error");
      }
    } catch (err) {
      console.error(err);
      this.showToast("Network error deleting item.", "error");
    }
  },
};

document.addEventListener("DOMContentLoaded", () => SkyVault.init());
