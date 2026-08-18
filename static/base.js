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
    if (saved === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  },

  bindThemeToggle() {
    const btn = document.getElementById("theme-toggle");
    if (!btn) return;
    btn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      if (next === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
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

  // Upload Confirmation Modal methods
  openUploadConfirmModal(data) {
    const modal = document.getElementById("upload-confirm-modal");
    const folderIdInput = document.getElementById("upload-confirm-folder-id");
    const fileIdInput = document.getElementById("upload-confirm-file-id");
    const fileNameInput = document.getElementById("upload-confirm-file-name");
    const suggestedCategoryEl = document.getElementById("upload-confirm-suggested-category");

    if (!modal) return;

    if (folderIdInput) folderIdInput.value = data.folder_id || "";
    if (fileIdInput) fileIdInput.value = data.file_id || "";
    if (fileNameInput) fileNameInput.value = data.file_name || "";
    if (suggestedCategoryEl) suggestedCategoryEl.textContent = data.category || "General";

    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    setTimeout(() => fileNameInput?.focus(), 100);
  },

  closeUploadConfirmModal(reload = true) {
    const modal = document.getElementById("upload-confirm-modal");
    if (modal) {
      modal.classList.remove("open");
      modal.setAttribute("aria-hidden", "true");
    }
    if (reload) {
      setTimeout(() => location.reload(), 300);
    }
  },

  async submitUploadConfirm(event) {
    if (event) event.preventDefault();

    const folderId = document.getElementById("upload-confirm-folder-id")?.value;
    const fileId = document.getElementById("upload-confirm-file-id")?.value;
    const fileName = document.getElementById("upload-confirm-file-name")?.value;

    try {
      const res = await fetch("/vault/confirm-upload-details/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": this.getCsrfToken(),
        },
        body: JSON.stringify({
          folder_id: folderId,
          file_id: fileId,
          file_name: fileName,
        }),
      });

      const data = await res.json();
      if (data.success) {
        this.showToast(data.message || "Upload details confirmed!", "success");
        this.closeUploadConfirmModal(true);
      } else {
        this.showToast(data.error || "Failed to update upload details.", "error");
      }
    } catch (err) {
      console.error(err);
      this.showToast("Network error submitting confirmation.", "error");
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

  // Render simple markdown: **bold**, *italic*, newlines → <br>, [n] citations
  renderMarkdown(text) {
    if (!text) return "";
    return this.escapeHtml(text)
      // **bold**
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      // *italic*
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      // [1][2] citation chips
      .replace(/\[(\d+)\]/g, '<sup style="font-size:10px;opacity:.7;">[$1]</sup>')
      // newlines
      .replace(/\n/g, "<br>");
  },

  // In-App File Preview Overlay Modal
  openPreviewModal(fileId) {
    const modal = document.getElementById("preview-modal");
    const title = document.getElementById("preview-title");
    const icon = document.getElementById("preview-icon");
    const body = document.getElementById("preview-body");
    const aiContent = document.getElementById("preview-ai-content");
    const openBtn = document.getElementById("preview-open-btn");
    const downloadBtn = document.getElementById("preview-download-btn");

    if (!modal) return;

    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    body.innerHTML = '<div class="spinner-container"><span class="material-icons spinner">sync</span> Loading preview...</div>';

    // Reset action buttons while loading
    if (openBtn) openBtn.style.display = "none";
    if (downloadBtn) downloadBtn.href = `/vault/download-file/${fileId}/`;

    fetch(`/vault/preview-file/${fileId}/`)
      .then((res) => res.json())
      .then((data) => {
        if (!data.success) {
          body.innerHTML = `<p class="error-msg">Unable to load preview.</p>`;
          return;
        }

        title.textContent = data.name;
        const ext = data.extension;
        const fileUrl = data.url;
        const downloadUrl = `/vault/download-file/${fileId}/`;

        // Wire header action buttons
        if (downloadBtn) {
          downloadBtn.href = downloadUrl;
          downloadBtn.setAttribute("download", data.name);
        }

        if (["jpg", "jpeg", "png", "gif", "webp", "svg"].includes(ext)) {
          icon.textContent = "image";
          // Images: show open button that launches the in-app viewer
          if (openBtn) {
            openBtn.style.display = "flex";
            openBtn.onclick = (e) => { e.preventDefault(); this.openDocViewer(fileUrl, data.name, "image", downloadUrl); };
          }
          body.innerHTML = `<div class="image-preview-wrapper"><img src="${fileUrl}" alt="${data.name}" class="preview-img"></div>`;
        } else if (ext === "pdf") {
          icon.textContent = "picture_as_pdf";
          if (openBtn) {
            openBtn.style.display = "flex";
            openBtn.onclick = (e) => { e.preventDefault(); this.openDocViewer(fileUrl, data.name, "pdf", downloadUrl); };
          }
          body.innerHTML = `
            <div class="pdf-preview-container">
              <iframe src="${fileUrl}" class="pdf-inline-frame" title="${this.escapeHtml(data.name)}"></iframe>
            </div>`;
        } else if (["txt", "md", "json", "py", "js", "html", "css"].includes(ext)) {
          icon.textContent = "description";
          if (openBtn) {
            openBtn.style.display = "flex";
            openBtn.onclick = (e) => { e.preventDefault(); this.openDocViewer(fileUrl, data.name, "text", downloadUrl); };
          }
          body.innerHTML = `<pre class="preview-code skyvault-scroll">${this.escapeHtml(data.text_content || "")}</pre>`;
        } else {
          icon.textContent = "insert_drive_file";
          if (openBtn) openBtn.style.display = "none";
          body.innerHTML = `
            <div class="download-preview-box">
              <span class="material-icons big-icon">insert_drive_file</span>
              <p>No inline preview available for .${ext} files.</p>
              <a href="${downloadUrl}" download="${data.name}" class="btn btn-primary">Download File</a>
            </div>`;
        }

        // Render AI analysis slot
        aiContent.innerHTML = this.renderAiAnalysis(data.ai_analysis);
      })
      .catch((err) => {
        console.error("Preview error:", err);
        body.innerHTML = `<p class="error-msg">Error loading file preview.</p>`;
      });
  },

  openDocViewer(fileUrl, fileName, fileType, downloadUrl) {
    const viewerModal = document.getElementById("doc-viewer-modal");
    const iframe = document.getElementById("doc-viewer-iframe");
    const titleEl = document.getElementById("doc-viewer-title");
    const iconEl = document.getElementById("doc-viewer-icon");
    const dlBtn = document.getElementById("doc-viewer-download-btn");

    if (!viewerModal || !iframe) return;

    titleEl.textContent = fileName;
    iconEl.textContent = fileType === "pdf" ? "picture_as_pdf" : fileType === "image" ? "image" : "description";
    if (dlBtn) { dlBtn.href = downloadUrl; dlBtn.setAttribute("download", fileName); }

    iframe.src = "";
    viewerModal.classList.add("open");
    viewerModal.setAttribute("aria-hidden", "false");

    // Small delay so the modal is visible before iframe starts loading
    setTimeout(() => { iframe.src = fileUrl; }, 80);
  },

  closeDocViewer() {
    const viewerModal = document.getElementById("doc-viewer-modal");
    const iframe = document.getElementById("doc-viewer-iframe");
    if (viewerModal) {
      viewerModal.classList.remove("open");
      viewerModal.setAttribute("aria-hidden", "true");
    }
    if (iframe) iframe.src = "";
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
        ? `<p class="flex items-center gap-1.5 mt-3 text-xs text-[var(--text-primary)]"><span class="material-icons text-base text-[var(--accent-color)] shrink-0">folder_open</span> Suggested folder: <strong class="font-semibold">${this.escapeHtml(ai.suggested_folder)}</strong></p>`
        : "";
      return `
        <p class="text-xs leading-relaxed text-[var(--text-primary)]"><strong>Summary:</strong> ${this.escapeHtml(ai.summary || "")}</p>
        <div class="flex flex-wrap gap-1.5 my-3">${chips}</div>
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

  openPreviewFromRag(fileId) {
    // Open preview overlay in front (z-index: 3000) without closing RAG chat modal behind it
    this.openPreviewModal(fileId);
  },

  isChitchatQuery(query) {
    const chitchatSet = new Set([
      "hi", "hello", "hey", "heya", "greetings", "good morning", "good afternoon", "good evening",
      "how are you", "how are you doing", "whats up", "what's up", "who are you", "what are you",
      "what can you do", "who created you", "thanks", "thank you", "thx", "bye", "goodbye",
      "cool", "awesome", "great", "ok", "okay", "help", "im doing great", "i am doing great",
      "doing good", "doing great", "fine", "good"
    ]);
    const cleaned = (query || "").toLowerCase().replace(/[^\w\s]/g, "").trim();
    if (chitchatSet.has(cleaned)) return true;
    const words = cleaned.split(/\s+/);
    return words.length <= 4 && words.some(w => chitchatSet.has(w));
  },

  getRagHistoryKey() {
    return "skyvault_rag_chat_history";
  },

  loadRagHistory() {
    const chatBody = document.getElementById("rag-chat-body");
    if (!chatBody) return;

    try {
      const raw = localStorage.getItem(this.getRagHistoryKey());
      if (!raw) return;
      const history = JSON.parse(raw);
      if (!Array.isArray(history) || history.length === 0) return;

      // Keep default system welcome message, append saved messages
      history.forEach((msg) => {
        if (msg.role === "user") {
          const userMsg = document.createElement("div");
          userMsg.className = "rag-message user-msg";
          userMsg.textContent = msg.text || "";
          chatBody.appendChild(userMsg);
        } else if (msg.role === "ai") {
          const aiMsg = document.createElement("div");
          aiMsg.className = "rag-message ai-msg";

          let sourcesHtml = "";
          if (msg.sources && msg.sources.length > 0) {
            sourcesHtml = `<div style="margin-top:12px; padding-top:10px; border-top:1px solid var(--border-color); font-size:12px; color:var(--text-secondary);">
              <strong>Cited Sources:</strong>
              <div style="display:flex; gap:6px; flex-wrap:wrap; margin-top:6px;">
                ${msg.sources.map(s => `<span onclick="SkyVault.openPreviewFromRag(${s.id})" class="chip" style="cursor:pointer;"><span class="material-icons" style="font-size:12px; vertical-align:middle;">description</span> ${this.escapeHtml(s.name)}</span>`).join("")}
              </div>
            </div>`;
          }

          aiMsg.innerHTML = `
            <span class="material-icons"></span>
            <div style="flex:1;">
              <p style="margin:0; font-size:14px; line-height:1.6;">${this.renderMarkdown(msg.answer || "")}</p>
              ${sourcesHtml}
            </div>`;
          chatBody.appendChild(aiMsg);
        }
      });
      chatBody.scrollTop = chatBody.scrollHeight;
    } catch (e) {
      console.warn("Failed to load RAG chat history:", e);
    }
  },

  saveRagMessage(item) {
    try {
      const raw = localStorage.getItem(this.getRagHistoryKey());
      const history = raw ? JSON.parse(raw) : [];
      history.push(item);
      if (history.length > 50) history.shift();
      localStorage.setItem(this.getRagHistoryKey(), JSON.stringify(history));
    } catch (e) {
      console.warn("Failed to save RAG chat message:", e);
    }
  },

  clearRagHistory() {
    localStorage.removeItem(this.getRagHistoryKey());
    const chatBody = document.getElementById("rag-chat-body");
    if (chatBody) {
      chatBody.innerHTML = `
        <div class="rag-message system-msg">
            <span class="material-icons">auto_awesome</span>
            <div>
                <p style="font-weight:600;">Hi! I'm SkyVault AI.</p>
                <p class="subtext">Ask me any question about your documents, invoices, or notes. I'll search your vector embeddings and cite the exact source files.</p>
            </div>
        </div>`;
    }
    this.showToast("Chat history cleared", "info");
  },

  openRagModal() {
    const modal = document.getElementById("rag-chat-modal");
    if (modal) {
      if (!this._ragHistoryLoaded) {
        this.loadRagHistory();
        this._ragHistoryLoaded = true;
      }
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

    if (this._ragInFlight) return;

    const query = input.value.trim();
    if (!query) return;

    // Append user question message
    const userMsg = document.createElement("div");
    userMsg.className = "rag-message user-msg";
    userMsg.textContent = query;
    chatBody.appendChild(userMsg);
    this.saveRagMessage({ role: "user", text: query });

    input.value = "";
    chatBody.scrollTop = chatBody.scrollHeight;

    this._setRagBusy(true);

    // Append loading placeholder — text adapts to chitchat vs document queries
    const isChitchat = this.isChitchatQuery(query);
    const thinkingText = isChitchat ? "Thinking" : "Searching your files";
    const loadingMsg = document.createElement("div");
    loadingMsg.className = "rag-message-row";
    loadingMsg.innerHTML = `
      <div class="rag-message ai-msg loading-msg">
        <div class="ai-thinking-wrapper">
          <span class="material-icons ai-sparkle-pulse">auto_awesome</span>
          <span>${thinkingText}</span>
          <span class="thinking-dots">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </span>
        </div>
      </div>`;
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
        if (!ok || data.error) {
          this._appendRagError(chatBody, data.error || "Failed to get AI answer. Please try again.");
          return;
        }

        const aiMsg = document.createElement("div");
        aiMsg.className = "rag-message ai-msg";

        let sourcesHtml = "";
        if (data.sources && data.sources.length > 0) {
          sourcesHtml = `<div class="mt-3 pt-2.5 border-t border-[var(--border-color)] text-xs text-[var(--text-secondary)]">
            <strong class="font-semibold text-[var(--text-primary)]">Cited Sources:</strong>
            <div class="flex gap-1.5 flex-wrap mt-1.5">
              ${data.sources.map(s => `<span onclick="SkyVault.openPreviewFromRag(${s.id})" class="chip cursor-pointer hover:border-[var(--accent-color)] hover:text-[var(--accent-color)] transition-colors"><span class="material-icons text-xs align-middle">description</span> ${this.escapeHtml(s.name)}</span>`).join("")}
            </div>
          </div>`;
        }

        aiMsg.innerHTML = `
          <span class="material-icons text-[var(--accent-color)] shrink-0 mt-0.5">auto_awesome</span>
          <div class="flex-1 min-w-0">
            <p class="m-0 text-sm leading-relaxed text-[var(--text-primary)]">${this.renderMarkdown(data.answer || "")}</p>
            ${sourcesHtml}
          </div>`;
        chatBody.appendChild(aiMsg);
        chatBody.scrollTop = chatBody.scrollHeight;
        this.saveRagMessage({ role: "ai", answer: data.answer, sources: data.sources });
      })
      .catch((err) => {
        console.error("RAG Error:", err);
        this._appendRagError(chatBody, "Failed to get AI answer. Please try again.");
      })
      .finally(() => {
        chatBody.querySelectorAll(".rag-message-row").forEach((n) => n.remove());
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

  async emptyTrash() {
    this.hideContextMenus();
    const confirmed = await this.confirm({
      title: "Empty Trash",
      message: "Are you sure you want to permanently delete all items in the trash? This action CANNOT be undone.",
      confirmLabel: "Empty Trash",
      danger: true,
    });

    if (!confirmed) return;

    try {
      const res = await fetch("/vault/empty-trash/", {
        method: "POST",
        headers: {
          "X-CSRFToken": this.getCsrfToken(),
          "X-Requested-With": "XMLHttpRequest",
          "Accept": "application/json",
        },
      });
      const data = await res.json();
      if (data.success) {
        this.showToast(data.message || "Trash emptied successfully.", "success");
        setTimeout(() => location.reload(), 600);
      } else {
        this.showToast(data.error || "Error emptying trash.", "error");
      }
    } catch (err) {
      console.error(err);
      this.showToast("Network error emptying trash.", "error");
    }
  },
};

document.addEventListener("DOMContentLoaded", () => SkyVault.init());
