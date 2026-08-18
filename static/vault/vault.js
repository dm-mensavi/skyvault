/**
 * SkyVaultDrive – vault-page specific JS
 * Handles: right-click item context menu, delete (with SkyVault.confirm modal),
 * copy/cut/paste, star, open / preview actions.
 * Depends on SkyVault global object in base.js.
 */

const SkyVaultDrive = (() => {
  const csrfToken = () => SkyVault.getCsrfToken();
  let selectedItemId = null;
  let selectedItemType = null;
  let selectedItemName = '';

  // ─── Helpers ─────────────────────────────────────────────────────────────────
  function getCurrentFolderId() {
    // folder id stored on .drive-container or drive-header data-folder-id
    return document.querySelector('[data-folder-id]')?.dataset.folderId || null;
  }

  function hideContextMenu() {
    const menu = document.getElementById('item-context-menu');
    if (menu) menu.classList.remove('open');
    SkyVault.hideContextMenus?.();
  }

  function showItemContextMenu(x, y) {
    const menu = document.getElementById('item-context-menu');
    if (!menu) return;
    SkyVault.hideContextMenus?.();
    menu.style.left = `${x}px`;
    menu.style.top  = `${y}px`;
    menu.classList.add('open');
  }

  // ─── Create Folder Modal ─────────────────────────────────────────────────────
  function openCreateFolderModal() {
    const modal = document.getElementById('folder-modal');
    if (modal) {
      modal.classList.add('open');
      modal.setAttribute('aria-hidden', 'false');
      setTimeout(() => document.getElementById('new-folder-name')?.focus(), 100);
    }
  }

  function closeCreateFolderModal() {
    const modal = document.getElementById('folder-modal');
    if (modal) {
      modal.classList.remove('open');
      modal.setAttribute('aria-hidden', 'true');
    }
  }

  // ─── Delete (move to trash) ──────────────────────────────────────────────────
  async function deleteItem() {
    if (!selectedItemId || !selectedItemType) return;
    hideContextMenu();

    const confirmed = await SkyVault.confirm({
      title: 'Move to Trash',
      message: `Move "${selectedItemName}" to trash?`,
      confirmLabel: 'Move to Trash',
      danger: true,
    });
    if (!confirmed) return;

    try {
      const res = await fetch(`/vault/delete-${selectedItemType}/${selectedItemId}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken() },
      });
      if (res.ok) {
        SkyVault.showToast(`${selectedItemType === 'file' ? 'File' : 'Folder'} moved to trash.`, 'success');
        setTimeout(() => location.reload(), 600);
      } else {
        SkyVault.showToast('Error moving item to trash.', 'error');
      }
    } catch (err) {
      console.error(err);
      SkyVault.showToast('Network error.', 'error');
    }
  }

  // ─── Star/Unstar ────────────────────────────────────────────────────────────
  async function toggleStar() {
    if (!selectedItemId || !selectedItemType) return;
    hideContextMenu();

    try {
      const res = await fetch('/vault/toggle-star/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken(),
        },
        body: JSON.stringify({ item_id: selectedItemId, item_type: selectedItemType }),
      });
      const data = await res.json();
      SkyVault.showToast(data.message || 'Star toggled.', data.success ? 'success' : 'error');
      if (data.success) setTimeout(() => location.reload(), 600);
    } catch (err) {
      SkyVault.showToast('Error toggling star.', 'error');
    }
  }

  // ─── Copy / Cut / Paste ──────────────────────────────────────────────────────
  function copyItem() {
    if (!selectedItemId) return;
    sessionStorage.setItem('skyvault-clipboard', JSON.stringify({
      id: selectedItemId, type: selectedItemType, name: selectedItemName, action: 'copy',
    }));
    SkyVault.showToast(`"${selectedItemName}" copied to clipboard.`, 'info');
    hideContextMenu();
  }

  function cutItem() {
    if (!selectedItemId) return;
    sessionStorage.setItem('skyvault-clipboard', JSON.stringify({
      id: selectedItemId, type: selectedItemType, name: selectedItemName, action: 'cut',
    }));
    SkyVault.showToast(`"${selectedItemName}" cut to clipboard.`, 'info');
    hideContextMenu();
  }

  async function pasteItem() {
    const clipboard = JSON.parse(sessionStorage.getItem('skyvault-clipboard') || 'null');
    if (!clipboard) {
      SkyVault.showToast('Clipboard is empty.', 'info');
      return;
    }

    // Determine target folder: if right-clicked directly on a folder card, paste into that folder;
    // otherwise paste into the current page folder.
    let targetFolder = getCurrentFolderId();
    if (selectedItemType === 'folder' && selectedItemId) {
      targetFolder = selectedItemId;
    }

    try {
      const res = await fetch('/vault/paste/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
        body: JSON.stringify({
          item_id: clipboard.id,
          item_type: clipboard.type,
          action: clipboard.action,
          target_folder: targetFolder,
        }),
      });
      const data = await res.json();
      SkyVault.showToast(data.message || (data.success ? 'Pasted.' : 'Error pasting.'), data.success ? 'success' : 'error');
      if (data.success) {
        sessionStorage.removeItem('skyvault-clipboard');
        setTimeout(() => location.reload(), 600);
      }
    } catch (err) {
      SkyVault.showToast('Network error during paste.', 'error');
    }
  }

  // ─── Context menu binding ────────────────────────────────────────────────────
  function bindItemContextMenu() {
    const mainPanel = document.querySelector('.main-panel');
    if (!mainPanel) return;

    mainPanel.addEventListener('contextmenu', (e) => {
      const card = e.target.closest('.drive-card');
      if (!card) return; // let base.js global handler deal with empty space
      e.preventDefault();
      e.stopPropagation();

      selectedItemId   = card.dataset.id;
      selectedItemType = card.dataset.type;
      selectedItemName = card.dataset.name || card.querySelector('.card-title')?.textContent.trim() || '';

      showItemContextMenu(e.clientX, e.clientY);
    });

    document.addEventListener('click', hideContextMenu);
  }

  function bindContextMenuActions() {
    const safe = (id, fn) => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('click', fn);
    };

    safe('ctx-open', () => {
      if (!selectedItemId) return;
      if (selectedItemType === 'folder') {
        location.href = `/vault/folder/${selectedItemId}/`;
      } else if (selectedItemType === 'file') {
        window.open(`/vault/open-file/${selectedItemId}/`, '_blank');
      }
      hideContextMenu();
    });

    safe('ctx-preview', () => {
      if (!selectedItemId) return;
      if (selectedItemType === 'file') {
        SkyVault.openPreviewModal(selectedItemId);
      } else if (selectedItemType === 'folder') {
        location.href = `/vault/folder/${selectedItemId}/`;
      }
      hideContextMenu();
    });

    safe('ctx-cut',    cutItem);
    safe('ctx-copy',   copyItem);
    safe('ctx-paste',  pasteItem);
    safe('ctx-star',   toggleStar);
    safe('ctx-delete', deleteItem);
  }

  // ─── Dismiss folder modal on Escape ─────────────────────────────────────────
  function bindKeyboard() {
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeCreateFolderModal();
        SkyVault.closePreviewModal?.();
        hideContextMenu();
      }
    });
  }

  // ─── Override global triggerCreateFolder & triggerUpload ────────────────────
  function patchGlobalTriggers() {
    SkyVault.triggerCreateFolder = () => openCreateFolderModal();
    SkyVault.triggerUpload = () => {
      const inp = document.getElementById('uploaded-file');
      if (inp) inp.click();
      else SkyVault.showToast('Navigate to My Drive or a Folder to upload.', 'info');
    };
  }

  // ─── Message auto-dismiss ────────────────────────────────────────────────────
  function initMessageDismiss() {
    setTimeout(() => {
      document.querySelectorAll('#message-container .toast').forEach(el => el.remove());
    }, 5000);
  }

  // ─── File Upload Handler (Single & Multi-File) ────────────────────────────────
  async function handleFileUpload(input) {
    if (!input || !input.files || input.files.length === 0) return;

    const form = input.closest('form');
    if (!form) return;

    const formData = new FormData(form);
    const parentFolderId = formData.get('folder_id') || getCurrentFolderId();
    if (parentFolderId && !formData.get('folder_id')) {
      formData.set('folder_id', parentFolderId);
    }

    SkyVault.showToast('Uploading & categorizing file(s)...', 'info');

    try {
      const res = await fetch(form.action || '/vault/upload/', {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json',
          'X-CSRFToken': csrfToken(),
        },
        body: formData,
      });

      const data = await res.json();
      if (!data.success) {
        SkyVault.showToast(data.error || 'Upload failed.', 'error');
        return;
      }

      if (data.is_single) {
        // Single file upload: Open confirmation modal pre-filled
        SkyVault.openUploadConfirmModal(data);
      } else {
        // Multi-file upload: Auto-categorized toast and view refresh
        SkyVault.showToast(data.message || `Uploaded & auto-categorized ${data.count} files.`, 'success');
        setTimeout(() => location.reload(), 800);
      }
    } catch (err) {
      console.error(err);
      SkyVault.showToast('Network error uploading file. Submitting form...', 'error');
      form.submit();
    } finally {
      input.value = '';
    }
  }

  // ─── Init ────────────────────────────────────────────────────────────────────
  function init() {
    patchGlobalTriggers();
    bindItemContextMenu();
    bindContextMenuActions();
    bindKeyboard();
    initMessageDismiss();
  }

  document.addEventListener('DOMContentLoaded', init);

  return { openCreateFolderModal, closeCreateFolderModal, pasteItem, handleFileUpload };
})();