document.addEventListener("DOMContentLoaded", () => {
  // ADD MODAL
  const addBtn = document.getElementById("open-add-form");
  const addModal = document.getElementById("add-plan-modal");
  const closeAdd = document.getElementById("close-add-modal");
  const cancelAdd = document.getElementById("cancel-add-form");

  addBtn?.addEventListener("click", () => addModal.classList.remove("hidden"));
  closeAdd?.addEventListener("click", () => addModal.classList.add("hidden"));
  cancelAdd?.addEventListener("click", () => addModal.classList.add("hidden"));

  // EDIT MODAL
  const editModal = document.getElementById("edit-plan-modal");
  const closeEdit = document.getElementById("close-edit-modal");
  const cancelEdit = document.getElementById("cancel-edit-form");
  const editForm = document.getElementById("edit-plan-form");

  document.querySelectorAll(".edit-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      const card = e.target.closest(".plan-card");
      const planId = card.dataset.id;

      // Correct URL: /plans/<plan_id>/edit/
      editForm.action = `/plans/${planId}/edit/`;

      document.getElementById("edit-plan-id").value = planId;
      document.getElementById("edit-name").value = card.dataset.name;
      document.getElementById("edit-description").value = card.dataset.description;
      document.getElementById("edit-price").value = card.dataset.price;
      document.getElementById("edit-currency").value = card.dataset.currency;
      document.getElementById("edit-billing-cycle").value = card.dataset.billingCycle;
      document.getElementById("edit-vendor").value = card.dataset.vendor;
      document.getElementById("edit-utility-type").value = card.dataset.utilityType;
      document.getElementById("edit-is-active").checked = card.dataset.isActive === "True";

      editModal.classList.remove("hidden");
    });
  });

  [closeEdit, cancelEdit].forEach(btn => btn?.addEventListener("click", () => editModal.classList.add("hidden")));

  // DELETE MODAL
  const deleteModal = document.getElementById("delete-plan-modal");
  const deleteForm = document.getElementById("delete-plan-form");
  const deleteName = document.getElementById("delete-plan-name");
  const deleteId = document.getElementById("delete-plan-id");
  const cancelDelete = document.getElementById("cancel-delete-form");

  document.querySelectorAll(".delete-btn").forEach(btn => {
    btn.addEventListener("click", e => {
      const card = e.target.closest(".plan-card");
      const planId = card.dataset.id;
      const planName = card.dataset.name;

      // Correct URL: /plans/<plan_id>/delete/
      deleteForm.action = `/plans/${planId}/delete/`;

      deleteName.textContent = planName;
      deleteId.value = planId;

      deleteModal.classList.remove("hidden");
    });
  });

  cancelDelete?.addEventListener("click", () => deleteModal.classList.add("hidden"));
});
