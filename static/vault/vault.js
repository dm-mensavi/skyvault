//->Handle message alerts
document.addEventListener("DOMContentLoaded", function () {
	setTimeout(function () {
		let messages = document.querySelectorAll(".alert");
		messages.forEach(function (message) {
			message.style.display = "none";
		});
	}, 5000); // Adjust time as needed (5000 ms = 5 seconds)
});

   document.querySelector("[data-action='delete']").addEventListener("click", function () {
        if (selectedItemId && selectedItemType) {
            if (confirm(`Are you sure you want to delete this ${selectedItemType}?`)) {
                fetch(`/vault/delete-${selectedItemType}/${selectedItemId}/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken
                    }
                })
                .then(response => {
                    if (response.ok) {
                        showAlert(`${selectedItemType.charAt(0).toUpperCase() + selectedItemType.slice(1)} deleted successfully.`, "success");
                        location.reload();
                    } else {
                        showAlert(`Error deleting ${selectedItemType}.`, "danger");
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert("An error occurred while deleting.", "danger");
                });
            }
        }
        hideContextMenu();
    });

//$ Right click event listeners for filtering options
//$ Right click event listeners for filtering options
//$ Right click event listeners for filtering options
document.addEventListener("DOMContentLoaded", function () {
  const contextMenu = document.querySelector(".context-menu");
  const driveContainer = document.querySelector(".drive-container");
  const fileFolderItems = document.querySelectorAll(".file-folder-only"); // Select file/folder-specific items
  let selectedItemId = null;
  let selectedItemType = null;

  // Function to show the context menu at a specific position
  function showContextMenu(x, y) {
      contextMenu.style.top = `${y}px`;
      contextMenu.style.left = `${x}px`;
      contextMenu.style.display = "block";
  }

  // Function to hide the context menu
  function hideContextMenu() {
      contextMenu.style.display = "none";
  }

  // Function to control the visibility of file/folder-specific items
  function setFileFolderOptionsVisibility(visible) {
      fileFolderItems.forEach(item => {
          item.style.display = visible ? "block" : "none";
      });
  }

  // Event listener for right-click on drive container
  driveContainer.addEventListener("contextmenu", function (e) {
      e.preventDefault(); // Prevent the default context menu from showing
      hideContextMenu(); // Hide any existing context menu

      // Check if the click was on a file or folder
      const fileItem = e.target.closest(".file-item");
      if (fileItem) {
          // Right-clicked on a file or folder
          selectedItemId = fileItem.dataset.id;
          selectedItemType = fileItem.dataset.type;
          setFileFolderOptionsVisibility(true); // Show file/folder-specific options
      } else {
          // Right-clicked on empty space
          selectedItemId = null;
          selectedItemType = null;
          setFileFolderOptionsVisibility(false); // Hide file/folder-specific options
      }

      // Show the context menu at the clicked position
      showContextMenu(e.pageX, e.pageY);
  });

  // Hide the context menu when clicking elsewhere on the document
  document.addEventListener("click", function () {
      hideContextMenu();
  });
});

//$ Right click event listeners for filtering options
//$ Right click event listeners for filtering options
//$ Right click event listeners for filtering options

//->Event Listener for the "Open" Action
//->Event Listener for the "Open" Action
//->Event Listener for the "Open" Action

document.addEventListener("DOMContentLoaded", function () {
  const contextMenu = document.querySelector(".context-menu");
  const driveContainer = document.querySelector(".drive-container");
  const fileFolderItems = document.querySelectorAll(".file-folder-only");
  let selectedItemId = null;
  let selectedItemType = null;

  // Show the context menu at a specific position
  function showContextMenu(x, y) {
      contextMenu.style.top = `${y}px`;
      contextMenu.style.left = `${x}px`;
      contextMenu.style.display = "block";
  }

  // Hide the context menu
  function hideContextMenu() {
      contextMenu.style.display = "none";
  }

  // Toggle visibility of file/folder-specific options
  function setFileFolderOptionsVisibility(visible) {
      fileFolderItems.forEach(item => {
          item.style.display = visible ? "block" : "none";
      });
  }

  // Handle right-click on drive container
  driveContainer.addEventListener("contextmenu", function (e) {
      e.preventDefault();
      hideContextMenu();

      const fileItem = e.target.closest(".file-item");
      if (fileItem) {
          selectedItemId = fileItem.dataset.id;
          selectedItemType = fileItem.dataset.type; // "file" or "folder"
          setFileFolderOptionsVisibility(true);
      } else {
          selectedItemId = null;
          selectedItemType = null;
          setFileFolderOptionsVisibility(false);
      }

      showContextMenu(e.pageX, e.pageY);
  });

  // Hide context menu on clicking elsewhere
  document.addEventListener("click", function () {
      hideContextMenu();
  });

  // Add event listener for "Open" functionality
  document.querySelector("[data-action='open']").addEventListener("click", function () {
      if (selectedItemId && selectedItemType) {
          if (selectedItemType === "folder") {
              // Redirect to the folder's view page
              window.location.href = `/vault/folder/${selectedItemId}/`;
          } else if (selectedItemType === "file") {
              // Redirect to the file's open/download endpoint
              window.location.href = `/vault/open-file/${selectedItemId}/`;
          }
      }
      hideContextMenu();
  });
});


//->Event Listener for the "Open" Action
//->Event Listener for the "Open" Action
//->Event Listener for the "Open" Action


//!Copy, Cut, and Paste Actions
//!Copy, Cut, and Paste Actions
//!Copy, Cut, and Paste Actions
document.addEventListener("DOMContentLoaded", function () {
  const contextMenu = document.querySelector(".context-menu");
  const driveContainer = document.querySelector(".drive-container");
  const messageContainer = document.querySelector(".message-container");
  const fileFolderItems = document.querySelectorAll(".file-folder-only");
  const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  let selectedItemId = null;
  let selectedItemType = null;

    // Function to display alerts in the message container
    function showAlert(message, type = 'info') {
        if (messageContainer) {
            const alertDiv = document.createElement('div');
            alertDiv.classList.add('alert', `alert-${type}`);
            alertDiv.textContent = message;
            messageContainer.appendChild(alertDiv);
            setTimeout(() => alertDiv.remove(), 5000); // Auto-remove after 5 seconds
        }
    }

    // Event listener for "Star" functionality in the context menu
    document.querySelector("[data-action='star']").addEventListener("click", function () {
        if (selectedItemId && selectedItemType) {
            fetch(`/vault/toggle-star/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    item_id: selectedItemId,
                    item_type: selectedItemType
                })
            })
            .then(response => response.json())
            .then(data => {
                showAlert(data.message, data.success ? "success" : "danger");
                if (data.success) location.reload();  // Reload to reflect the updated star status
            })
            .catch(error => showAlert("An error occurred while toggling star status.", "danger"));
        }
        hideContextMenu();
    });

   document.querySelector("[data-action='delete']").addEventListener("click", function () {
        if (selectedItemId && selectedItemType) {
            if (confirm(`Are you sure you want to delete this ${selectedItemType}?`)) {
                fetch(`/vault/delete-${selectedItemType}/${selectedItemId}/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken
                    }
                })
                .then(response => {
                    if (response.ok) {
                        showAlert(`${selectedItemType.charAt(0).toUpperCase() + selectedItemType.slice(1)} deleted successfully.`, "success");
                        location.reload();
                    } else {
                        showAlert(`Error deleting ${selectedItemType}.`, "danger");
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert("An error occurred while deleting.", "danger");
                });
            }
        }
        hideContextMenu();
    });

  // Get the current folder ID from the data attribute
  const currentFolderId = driveContainer.dataset.folderId || null;
  let targetFolderId = currentFolderId;

  function showAlert(message, messageType = 'info') {
      // Use the existing message container to display messages
      if (messageContainer) {
          // Create a new alert div
          const alertDiv = document.createElement('div');
          alertDiv.classList.add('alert', `alert-${messageType}`);
          alertDiv.textContent = message;

          // Append the new alert to the message container
          messageContainer.appendChild(alertDiv);

          // Remove the alert after 5 seconds
          setTimeout(() => {
              alertDiv.remove();
          }, 5000);
      } else {
          // If messageContainer doesn't exist, create it
          const newMessageContainer = document.createElement('div');
          newMessageContainer.classList.add('message-container');
          document.body.prepend(newMessageContainer);

          const alertDiv = document.createElement('div');
          alertDiv.classList.add('alert', `alert-${messageType}`);
          alertDiv.textContent = message;
          newMessageContainer.appendChild(alertDiv);

          // Remove the alert after 5 seconds
          setTimeout(() => {
              alertDiv.remove();
          }, 5000);
      }
  }

  // Show the context menu at a specific position
  function showContextMenu(x, y) {
      contextMenu.style.top = `${y}px`;
      contextMenu.style.left = `${x}px`;
      contextMenu.style.display = "block";
  }

  // Hide the context menu
  function hideContextMenu() {
      contextMenu.style.display = "none";
  }

  // Toggle visibility of file/folder-specific options
  function setFileFolderOptionsVisibility(visible) {
      fileFolderItems.forEach(item => {
          item.style.display = visible ? "block" : "none";
      });
  }

  // Handle right-click on drive container
  driveContainer.addEventListener("contextmenu", function (e) {
      e.preventDefault();
      hideContextMenu();

      const fileItem = e.target.closest(".file-item");
      if (fileItem) {
          selectedItemId = fileItem.dataset.id;
          selectedItemType = fileItem.dataset.type; // "file" or "folder"
          setFileFolderOptionsVisibility(true);
          // Do not change targetFolderId; it should remain as the current folder
      } else {
          selectedItemId = null;
          selectedItemType = null;
          setFileFolderOptionsVisibility(false);
      }

      showContextMenu(e.pageX, e.pageY);
  });

  // Hide context menu on clicking elsewhere
  document.addEventListener("click", function () {
      hideContextMenu();
  });

  // Add event listener for "Copy" functionality
  document.querySelector("[data-action='copy']").addEventListener("click", function () {
      if (selectedItemId && selectedItemType) {
          sessionStorage.setItem("clipboard", JSON.stringify({
              id: selectedItemId,
              type: selectedItemType,
              action: "copy"
          }));
          showAlert("Item copied to clipboard!", "success");
      }
      hideContextMenu();
  });

  // Add event listener for "Cut" functionality
  document.querySelector("[data-action='cut']").addEventListener("click", function () {
      if (selectedItemId && selectedItemType) {
          sessionStorage.setItem("clipboard", JSON.stringify({
              id: selectedItemId,
              type: selectedItemType,
              action: "cut"
          }));
          showAlert("Item cut to clipboard!", "success");
      }
      hideContextMenu();
  });

  // Add event listener for "Paste" functionality
  document.querySelector("[data-action='paste']").addEventListener("click", function () {
      const clipboardData = JSON.parse(sessionStorage.getItem("clipboard"));
      if (clipboardData) {
          fetch(`/vault/paste/`, {
              method: "POST",
              headers: {
                  "Content-Type": "application/json",
                  "X-CSRFToken": csrfToken
              },
              body: JSON.stringify({
                  item_id: clipboardData.id,
                  item_type: clipboardData.type,
                  action: clipboardData.action,
                  target_folder: targetFolderId
              })
          })
          .then(response => response.json())
          .then(data => {
              if (data.success) {
                  showAlert(data.message, "success");
                  location.reload(); // Reload to show the pasted item
              } else {
                  showAlert("Error: " + data.message, "danger");
              }
          })
          .catch(error => {
              console.error('Error:', error);
              showAlert("An error occurred while pasting.", "danger");
          });
          sessionStorage.removeItem("clipboard");
      } else {
          showAlert("Clipboard is empty!", "warning");
      }
      hideContextMenu();
  });

  // Add event listener for "Open" functionality
  document.querySelector("[data-action='open']").addEventListener("click", function () {
      if (selectedItemId && selectedItemType) {
          if (selectedItemType === "folder") {
              // Redirect to the folder's view page
              window.location.href = `/vault/folder/${selectedItemId}/`;
          } else if (selectedItemType === "file") {
              // Redirect to the file's open/download endpoint
              window.location.href = `/vault/open-file/${selectedItemId}/`;
          }
      }
      hideContextMenu();
  });

  //delete event listener
  
});


//!Copy, Cut, and Paste Actions
//!Copy, Cut, and Paste Actions
//!Copy, Cut, and Paste Actions

//->Handle star
//->Handle star
//->Handle star