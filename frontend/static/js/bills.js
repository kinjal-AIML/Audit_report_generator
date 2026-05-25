document.addEventListener('DOMContentLoaded', () => {
  // Modal references
  const modals = {
    addBill: document.getElementById('addBillModal'),
    editBill: document.getElementById('editBillModal'),
    deleteBill: document.getElementById('deleteBillModal'),
    addCycle: document.getElementById('addCycleModal'),
    editCycle: document.getElementById('editCycleModal'),
    deleteCycle: document.getElementById('deleteCycleModal'),
    billDetails: document.getElementById('billDetailsModal'),
  };

  // Buttons to open modals
  document.getElementById('openAddBillModal').addEventListener('click', () => {
    modals.addBill.style.display = 'block';
  });
  document.getElementById('openAddCycleModal').addEventListener('click', () => {
    modals.addCycle.style.display = 'block';
  });

  // Close buttons on modals (X buttons)
  document.querySelectorAll('.modal .close').forEach(closeBtn => {
    closeBtn.addEventListener('click', e => {
      e.target.closest('.modal').style.display = 'none';
    });
  });

  // Close buttons with class 'close-btn' (Cancel buttons)
  document.querySelectorAll('.close-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      e.target.closest('.modal').style.display = 'none';
    });
  });

  // Click outside modal content closes modal
  window.addEventListener('click', e => {
    Object.values(modals).forEach(modal => {
      if (e.target === modal) modal.style.display = 'none';
    });
  });

  // --- Bills ---

  // View Bill details modal
  document.querySelectorAll('.view-bill-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const bill = JSON.parse(btn.getAttribute('data-bill'));
      document.getElementById('modalUtility').textContent = bill.utility || '-';
      document.getElementById('modalVendor').textContent = bill.vendor || '-';
      document.getElementById('modalBillingMonth').textContent = bill.billing_month || '-';
      document.getElementById('modalDueDate').textContent = bill.due_date || '-';
      document.getElementById('modalAmount').textContent = `₹${bill.amount || '-'} ${bill.currency || ''}`;
      document.getElementById('modalStatus').textContent = bill.payment_status || '-';
      document.getElementById('modalPaymentDate').textContent = bill.payment_date || '-';
      document.getElementById('modalNotes').textContent = bill.notes || '-';
      if (bill.file && bill.file !== '-') {
        document.getElementById('modalFile').innerHTML = `<a href="${bill.file}" target="_blank">Download</a>`;
      } else {
        document.getElementById('modalFile').textContent = '-';
      }
      modals.billDetails.style.display = 'block';
    });
  });

  // Edit Bill modal
  document.querySelectorAll('.edit-bill-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const bill = JSON.parse(btn.getAttribute('data-bill'));
      // Fill form inputs
      document.getElementById('edit_utility_type').value = bill.utility_id || '';
      document.getElementById('edit_vendor').value = bill.vendor_id || '';
      document.getElementById('edit_billing_month').value = bill.billing_month || '';
      document.getElementById('edit_due_date').value = bill.due_date || '';
      document.getElementById('edit_amount').value = bill.amount || '';
      document.getElementById('edit_currency').value = bill.currency || 'INR';
      document.getElementById('edit_payment_status').value = bill.payment_status || 'unpaid';
      document.getElementById('edit_notes').value = bill.notes || '';

      // Set form action URL dynamically
      const form = document.getElementById('editBillForm');
      form.action = `/bills/${bill.id}/edit/`;

      modals.editBill.style.display = 'block';
    });
  });

  // Delete Bill modal
  document.querySelectorAll('.delete-bill-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const billId = btn.getAttribute('data-id');
      const form = document.getElementById('deleteBillForm');
      form.action = `/bills/${billId}/delete/`;
      modals.deleteBill.style.display = 'block';
    });
  });

  // --- Billing Cycles ---

  // Edit Cycle modal
  document.querySelectorAll('.edit-cycle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const cycle = JSON.parse(btn.getAttribute('data-cycle'));

      document.getElementById('edit_cycle_start').value = cycle.cycle_start || '';
      document.getElementById('edit_cycle_end').value = cycle.cycle_end || '';
      document.getElementById('edit_expected_payment_date').value = cycle.expected_payment_date || '';
      // For "Is Active" dropdown, set value instead of checked because it's a <select>
      if (cycle.is_active === true || cycle.is_active === 'true' || cycle.is_active === 1) {
        document.getElementById('edit_is_active').value = 'true';
      } else {
        document.getElementById('edit_is_active').value = 'false';
      }

      // Set form action URL dynamically
      const form = document.getElementById('editCycleForm');
      form.action = `/billing-cycles/${cycle.id}/edit/`;

      modals.editCycle.style.display = 'block';
    });
  });

  // Delete Cycle modal
  document.querySelectorAll('.delete-cycle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const cycleId = btn.getAttribute('data-id');
      const form = document.getElementById('deleteCycleForm');
      form.action = `/billing-cycles/${cycleId}/delete/`;
      modals.deleteCycle.style.display = 'block';
    });
  });

  // --- Chart.js Rendering ---
  const ctx = document.getElementById('billingChart').getContext('2d');

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: window.billingLabels || [],
      datasets: [
        {
          label: 'Amount Due',
          data: window.billingValues || [],
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          fill: false,
          tension: 0.3
        },
        {
          label: 'Amount Paid',
          data: window.billingValuesPaid || [],
          borderColor: 'rgba(255, 99, 132, 1)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          fill: false,
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        title: {
          display: true,
          text: 'Billing Cycle Trend'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Amount (₹)'
          }
        },
        x: {
          title: {
            display: true,
            text: 'Billing Month'
          }
        }
      }
    }
  });
});
document.addEventListener('DOMContentLoaded', () => {
  const ctx = document.getElementById('billingChart').getContext('2d');

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: window.billingLabels,
      datasets: [
        {
          label: 'Amount Due',
          data: window.billingValues,
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          fill: false,
          tension: 0.3
        },
        {
          label: 'Amount Paid',
          data: window.billingValuesPaid,
          borderColor: 'rgba(255, 99, 132, 1)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          fill: false,
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        title: { display: true, text: 'Billing Cycle Trend' }
      },
      scales: {
        y: { beginAtZero: true, title: { display: true, text: 'Amount (₹)' } },
        x: { title: { display: true, text: 'Billing Month' } }
      }
    }
  });
});