document.addEventListener('DOMContentLoaded', () => {
  // Modal elements
  const addModal = document.getElementById('add-vendor-modal');
  const viewModal = document.getElementById('view-vendor-modal');
  const editModal = document.getElementById('edit-vendor-modal');
  const deleteModal = document.getElementById('delete-vendor-modal');

  // Open add modal button and close button
  const openAddBtn = document.getElementById('open-add-form');
  const closeAddBtn = document.getElementById('close-add-modal');

  openAddBtn.addEventListener('click', () => {
    addModal.classList.remove('hidden');
  });

  closeAddBtn.addEventListener('click', () => {
    addModal.classList.add('hidden');
  });

  // Close modals when clicking outside modal content
  [addModal, viewModal, editModal, deleteModal].forEach(modal => {
    modal.addEventListener('click', e => {
      if (e.target === modal) {
        modal.classList.add('hidden');
      }
    });
  });

  // Close buttons for other modals
  document.getElementById('close-view-modal').addEventListener('click', () => viewModal.classList.add('hidden'));
  document.getElementById('close-edit-modal').addEventListener('click', () => editModal.classList.add('hidden'));
  document.getElementById('close-delete-modal').addEventListener('click', () => deleteModal.classList.add('hidden'));
  document.getElementById('cancel-delete-btn').addEventListener('click', () => deleteModal.classList.add('hidden'));

  // Elements inside view modal
  const viewName = document.getElementById('view-name');
  const viewUtilityType = document.getElementById('view-utility-type');
  const viewCreatedAt = document.getElementById('view-created-at');
  const viewUpdatedAt = document.getElementById('view-updated-at');

  // Elements inside edit modal
  const editForm = document.getElementById('edit-vendor-form');
  const editNameInput = document.getElementById('edit-name');
  const editUtilityTypeSelect = document.getElementById('edit-utility-type');

  // Elements inside delete modal
  const deleteForm = document.getElementById('delete-vendor-form');
  const deleteVendorNameSpan = document.getElementById('delete-vendor-name');

  // Handle clicking on View, Edit, Delete icons
  document.querySelectorAll('.view-vendor').forEach(btn => {
    btn.addEventListener('click', () => {
      const tr = btn.closest('tr');
      const id = tr.dataset.id;

      // Fill modal with info
      viewName.textContent = tr.children[0].textContent;
      viewUtilityType.textContent = tr.children[1].textContent;
      viewCreatedAt.textContent = tr.children[2].textContent;
      viewUpdatedAt.textContent = tr.children[3].textContent;

      viewModal.classList.remove('hidden');
    });
  });

  document.querySelectorAll('.edit-vendor').forEach(btn => {
    btn.addEventListener('click', () => {
      const tr = btn.closest('tr');
      const id = tr.dataset.id;

      // Fill form with current values
      editNameInput.value = tr.children[0].textContent;

      // Select correct utility_type_id
      const utilityId = tr.children[1].textContent.trim();
      for (const option of editUtilityTypeSelect.options) {
        option.selected = option.value === utilityId;
      }

      // Set form action dynamically to edit URL (adjust to your URL pattern)
      editForm.action = `/vendors/${id}/edit/`;


      editModal.classList.remove('hidden');
    });
  });

  document.querySelectorAll('.delete-vendor').forEach(btn => {
    btn.addEventListener('click', () => {
      const tr = btn.closest('tr');
      const id = tr.dataset.id;
      const name = tr.children[0].textContent;

      deleteVendorNameSpan.textContent = name;
      deleteForm.action = `/vendors/${id}/delete/`;


      deleteModal.classList.remove('hidden');
    });
  });

});
