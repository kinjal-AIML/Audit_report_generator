
document.addEventListener("DOMContentLoaded", function () {
  const nameField = document.getElementById("id_Employee_name");
  const auditManagerField  = document.getElementById("id_audit_manager");
  const partnerField = document.getElementById("id_Partner");
  const adminField = document.getElementById("id_Admin");
  const deleteBtn = document.getElementById("delete-btn");

  // Create suggestion box for autocomplete
  const suggestionBox = document.createElement("div");
  suggestionBox.style.border = "1px solid #ccc";
  suggestionBox.style.position = "absolute";
  suggestionBox.style.backgroundColor = "white";
  suggestionBox.style.zIndex = 1000;
  suggestionBox.style.maxHeight = "150px";
  suggestionBox.style.overflowY = "auto";
  suggestionBox.style.width = nameField.offsetWidth + "px";
  suggestionBox.style.display = "none";
  nameField.parentNode.style.position = "relative";
  nameField.parentNode.appendChild(suggestionBox);

  // Function to clear suggestions
  function clearSuggestions() {
    suggestionBox.innerHTML = "";
    suggestionBox.style.display = "none";
  }

  // Helper to get CSRF token from cookies
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrftoken = getCookie('csrftoken');

  // Autofill other fields based on employee name
  function autofillDetails(name) {
    fetch(`/get-employee-details/?name=${encodeURIComponent(name)}`)
      .then(response => response.json())
      .then(data => {
        if (data.found) {
          auditManagerField .value = data.audit_manager|| "";
          partnerField.value = data.Partner || "";
          adminField.value = data.Admin || "";
          deleteBtn.disabled = false;  // Enable delete button when employee found
        } else {
          auditManagerField .value = "";
          partnerField.value = "";
          adminField.value = "";
          deleteBtn.disabled = true;  // Disable delete button if not found
        }
      })
      .catch(console.error);
  }

  // Listen to input for autocomplete
  nameField.addEventListener("input", function () {
    const val = this.value.trim();
    if (val.length < 1) {
      clearSuggestions();
      deleteBtn.disabled = true;  // disable delete if no input
      auditManagerField .value = "";
      partnerField.value = "";
      adminField.value = "";
      return;
    }
    fetch(`/employee-name-autocomplete/?term=${encodeURIComponent(val)}`)
      .then(response => response.json())
      .then(names => {
        suggestionBox.innerHTML = "";
        if (names.length === 0) {
          clearSuggestions();
          deleteBtn.disabled = true;
          return;
        }
        names.forEach(name => {
          const div = document.createElement("div");
          div.textContent = name;
          div.style.padding = "5px";
          div.style.cursor = "pointer";
          div.addEventListener("mousedown", function (e) {
            e.preventDefault(); // prevent losing focus
            nameField.value = name;
            clearSuggestions();
            autofillDetails(name);
          });
          suggestionBox.appendChild(div);
        });
        suggestionBox.style.display = "block";
      });
  });

  // Hide suggestions on clicking outside
  document.addEventListener("click", function (e) {
    if (!suggestionBox.contains(e.target) && e.target !== nameField) {
      clearSuggestions();
    }
  });

  // Delete button click handler
  deleteBtn.addEventListener("click", function () {
    const employeeName = nameField.value.trim();
    if (!employeeName) return;

    if (confirm(`Are you sure you want to delete employee "${employeeName}"?`)) {
      fetch(`/delete-employee/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ Employee_name: employeeName }),
      })
      .then(response => response.json())
      .then(data => {
        if (data.deleted) {
          alert(`Employee "${employeeName}" deleted successfully.`);
          form.reset();
          // Clear all form fields
          nameField.value = "";
          auditManagerField .value = "";
          partnerField.value = "";
          adminField.value = "";
          deleteBtn.disabled = true;
        } else {
          alert(data.error || "Failed to delete employee.");
        }
      })
      .catch(console.error);
    }
  });

});

