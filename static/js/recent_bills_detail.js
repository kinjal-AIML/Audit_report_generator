document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('billing-modal');
  const form = document.getElementById('billing-form');
  const modalCloseButtons = modal.querySelectorAll('.modal-close');
  const addBtn = document.getElementById('add-bill-btn');

  // Open modal for adding new bill
  addBtn.addEventListener('click', () => {
    openModal();
    clearForm();
  });

  // Open modal for editing bill (delegation for edit buttons)
  document.querySelectorAll('.edit-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      openModal();

      // Fill form with data attributes
      form.id.value = btn.dataset.id || '';
      form.user_id.value = btn.dataset.user_id || '';
      form.utility_type_id.value = btn.dataset.utility_type_id || '';
      form.vendor_id.value = btn.dataset.vendor_id || '';
      form.billing_month.value = btn.dataset.billing_month || '';
      form.due_date.value = btn.dataset.due_date || '';
      form.cycle_start.value = btn.dataset.cycle_start || '';
      form.cycle_end.value = btn.dataset.cycle_end || '';
      form.amount.value = btn.dataset.amount || '';
      form.amount_due.value = btn.dataset.amount_due || '';
      form.amount_paid.value = btn.dataset.amount_paid || '';
      form.currency.value = btn.dataset.currency || 'USD';
      form.payment_status.value = btn.dataset.payment_status || 'unpaid';
      form.payment_date.value = btn.dataset.payment_date || '';
      form.file_path.value = btn.dataset.file_path || '';
      form.file_name.value = btn.dataset.file_name || '';
      form.file_mime.value = btn.dataset.file_mime || '';
      form.notes.value = btn.dataset.notes || '';
    });
  });

  // Close modal handlers
  modalCloseButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      closeModal();
    });
  });

  // Close modal on clicking outside modal-content
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeModal();
    }
  });

  // Helpers
  function openModal() {
    modal.classList.add('visible');
  }

  function closeModal() {
    modal.classList.remove('visible');
  }

  function clearForm() {
    form.reset();
    form.id.value = '';
    form.currency.value = 'USD';
    form.payment_status.value = 'unpaid';
    form.amount_paid.value = 0;
  }
});
