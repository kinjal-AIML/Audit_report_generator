document.addEventListener('DOMContentLoaded', () => {
  // Modal elements
  const addModal = document.getElementById('add-utility-modal');
  const viewModal = document.getElementById('view-utility-modal');
  const editModal = document.getElementById('edit-utility-modal');
  const deleteModal = document.getElementById('delete-utility-modal');

  // Buttons / spans that open/close modals
  const openAddBtn = document.getElementById('open-add-form');
  const closeAddBtn = document.getElementById('close-add-modal');

  const closeViewBtn = document.getElementById('close-view-modal');
  const closeEditBtn = document.getElementById('close-edit-modal');
  const closeDeleteBtn = document.getElementById('close-delete-modal');

  const editForm = document.getElementById('edit-utility-form');
  const deleteForm = document.getElementById('delete-utility-form');

  const viewName = document.getElementById('view-name');
  const viewReminder = document.getElementById('view-reminder');
  const viewDueDate = document.getElementById('view-due-date');
  const viewCreated = document.getElementById('view-created');
  const viewUpdated = document.getElementById('view-updated');

  const deleteUtilityNameElem = document.getElementById('delete-utility-name');

  // --- Add modal open/close ---
  openAddBtn.addEventListener('click', () => {
    addModal.classList.remove('hidden');
  });
  closeAddBtn.addEventListener('click', () => {
    addModal.classList.add('hidden');
  });
  addModal.addEventListener('click', (e) => {
    if (e.target === addModal) {
      addModal.classList.add('hidden');
    }
  });

  // --- View (eye icon) ---
  document.querySelectorAll('.view-utility').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const card = e.target.closest('.list-card');
      const name = card.querySelector('.util-name').textContent.trim();
      const reminder = card.querySelector('.util-reminder').textContent.trim();
      const dueDate = card.querySelector('.util-due-date')?.textContent.trim() || 'N/A';

      viewName.textContent = name;
      viewReminder.textContent = reminder;
      viewDueDate.textContent = dueDate;

      viewCreated.textContent = ''; // Optional: fill via AJAX
      viewUpdated.textContent = '';

      viewModal.classList.remove('hidden');
    });
  });
  closeViewBtn.addEventListener('click', () => {
    viewModal.classList.add('hidden');
  });
  viewModal.addEventListener('click', (e) => {
    if (e.target === viewModal) {
      viewModal.classList.add('hidden');
    }
  });

  // --- Edit ---
  document.querySelectorAll('.edit-utility').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const card = e.target.closest('.list-card');
      const id = btn.dataset.id;
      const name = card.querySelector('.util-name').textContent.trim();
      const reminder = card.querySelector('.util-reminder').textContent.trim();
      const dueDate = card.querySelector('.util-due-date')?.textContent.trim();

      document.getElementById('edit-name').value = name;
      document.getElementById('edit-reminder').value = reminder;

      if (dueDate && dueDate !== 'N/A') {
        document.getElementById('edit-due-date').value = formatDateForInput(dueDate);
      } else {
        document.getElementById('edit-due-date').value = '';
      }

      editForm.action = `/utilities/${id}/edit/`;
      editModal.classList.remove('hidden');
    });
  });
  closeEditBtn.addEventListener('click', () => {
    editModal.classList.add('hidden');
  });
  editModal.addEventListener('click', (e) => {
    if (e.target === editModal) {
      editModal.classList.add('hidden');
    }
  });

  // --- Delete ---
  document.querySelectorAll('.delete-utility').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const card = e.target.closest('.list-card');
      const id = btn.dataset.id;
      const name = card.querySelector('.util-name').textContent.trim();

      deleteUtilityNameElem.textContent = name;
      deleteForm.action = `/utilities/${id}/delete/`;

      deleteModal.classList.remove('hidden');
    });
  });
  closeDeleteBtn.addEventListener('click', () => {
    deleteModal.classList.add('hidden');
  });
  deleteModal.addEventListener('click', (e) => {
    if (e.target === deleteModal) {
      deleteModal.classList.add('hidden');
    }
  });

  // --- Utility: Convert date string (e.g., "2025-10-11") to yyyy-mm-dd for input[type="date"]
  function formatDateForInput(dateStr) {
    const date = new Date(dateStr);
    if (isNaN(date)) return '';
    return date.toISOString().split('T')[0];
  }

});
