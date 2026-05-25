let editingUserId = null;

// Elements
const addUserBtn = document.getElementById('addUserBtn');
const userModal = document.getElementById('userModal');
const closeUserModal = document.getElementById('closeUserModal');
const cancelUserBtn = document.getElementById('cancelUserBtn');
const userForm = document.getElementById('userForm');

// ---------------------
// Toast helper
// ---------------------
function showToast(message, type = 'success') {
  let toast = document.createElement('div');
  toast.className = `toast ${type}`; // type: 'success' or 'error'
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('show');
  }, 100); // small delay for animation

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => document.body.removeChild(toast), 300);
  }, 3000); // show for 3 seconds
}

// ---------------------
// Modal Open/Close
// ---------------------
addUserBtn.addEventListener('click', () => {
  userForm.reset();
  editingUserId = null;
  userForm.password.required = true;
  userModal.style.display = 'flex';
});

[closeUserModal, cancelUserBtn].forEach(btn =>
  btn.addEventListener('click', () => userModal.style.display = 'none')
);

window.addEventListener('click', (e) => {
  if (e.target === userModal) userModal.style.display = 'none';
});

// ---------------------
// Edit / Delete buttons
// ---------------------
document.querySelectorAll('.edit-user').forEach(btn => {
  btn.addEventListener('click', () => {
    editingUserId = btn.dataset.id;
    const row = btn.closest('tr');

    userForm.username.value = row.children[1].textContent;
    userForm.email.value = row.children[2].textContent;
    userForm.role.value = row.children[3].textContent;
    userForm.password.required = false;
    userForm.password.value = '';

    userModal.style.display = 'flex';
  });
});

document.querySelectorAll('.delete-user').forEach(btn => {
  btn.addEventListener('click', () => {
    if (confirm('Are you sure you want to delete this user?')) {
      deleteUser(btn.dataset.id);
    }
  });
});

// ---------------------
// AJAX functions
// ---------------------
async function saveEditedUser(userId, userData) {
  try {
    const res = await fetch(`/users/${userId}/update/`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    const data = await res.json();
    if (data.success) {
      showToast('User updated successfully!', 'success');
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast(data.error, 'error');
    }
  } catch (err) {
    showToast('Error updating user: ' + err, 'error');
  }
}

async function deleteUser(userId) {
  try {
    // <-- Updated URL here: moved 'delete' after userId to match Django URLs -->
    const res = await fetch(`/users/${userId}/delete/`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) {
      // If status code is not 2xx, get text and show it
      const text = await res.text();
      throw new Error(`Server error (${res.status}): ${text}`);
    }

    const data = await res.json();
    if (data.success) {
      showToast('User deleted successfully!', 'success');
      setTimeout(() => location.reload(), 1000);
    } else {
      showToast(data.error, 'error');
    }
  } catch (err) {
    showToast('Error deleting user: ' + err.message, 'error');
  }
}

// ---------------------
// Form submission
// ---------------------
userForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const userData = {
    name: userForm.username.value,
    email: userForm.email.value,
    role: userForm.role.value,
    password_hash: userForm.password.value || null
  };

  if (editingUserId) {
    await saveEditedUser(editingUserId, userData);
  } else {
    try {
      const res = await fetch('/users/add/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
      });
      const data = await res.json();
      if (data.success) {
        showToast('User added successfully!', 'success');
        setTimeout(() => location.reload(), 1000);
      } else {
        showToast(data.error, 'error');
      }
    } catch (err) {
      showToast('Error adding user: ' + err, 'error');
    }
  }

  userModal.style.display = 'none';
  editingUserId = null;
});
