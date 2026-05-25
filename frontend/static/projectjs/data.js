$(document).ready(function () {

  // Get CSRF token from cookies
  function getCSRFToken() {
    return document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];
  }

  // Switch row to edit mode
  function switchToEdit($row) {
    $row.find(".editable-cell").each(function () {
      const $cell = $(this);
      const field = $cell.data("field");
      const text = $cell.text().trim();

      // For boolean fields (Yes/No)
      if (field === "is_superuser" || field === "is_staff") {
        const select = $('<select class="form-control form-control-sm"></select>');
        select.append(`<option value="Yes" ${text === "Yes" ? "selected" : ""}>Yes</option>`);
        select.append(`<option value="No" ${text === "No" ? "selected" : ""}>No</option>`);
        $cell.html(select);
      } else {
        $cell.html(`<input type="text" class="form-control form-control-sm" value="${text}">`);
      }
    });

    $row.find(".btn-edit, .btn-delete").hide();
    $row.find(".btn-save, .btn-cancel").show();
  }

  // Switch row to view mode (after save or cancel)
  function switchToView($row, originalData = null) {
    $row.find(".editable-cell").each(function () {
      const $cell = $(this);
      const field = $cell.data("field");
      if (originalData && originalData[field] !== undefined) {
        // If cancel pressed, revert to original data
        if (field === "is_superuser" || field === "is_staff") {
          $cell.text(originalData[field] ? "Yes" : "No");
        } else {
          $cell.text(originalData[field]);
        }
      } else {
        // After save: get value from input/select
        let val;
        if ($cell.find("select").length) {
          val = $cell.find("select").val();
          if (field === "is_superuser" || field === "is_staff") {
            $cell.text(val === "Yes" ? "Yes" : "No");
          } else {
            $cell.text(val);
          }
        } else if ($cell.find("input").length) {
          val = $cell.find("input").val();
          $cell.text(val);
        }
      }
    });

    $row.find(".btn-save, .btn-cancel").hide();
    $row.find(".btn-edit, .btn-delete").show();
  }

  // Collect row data (key: field, value: input/select value)
  function collectRowData($row) {
    let data = {};
    $row.find(".editable-cell").each(function () {
      const $cell = $(this);
      const field = $cell.data("field");
      if ($cell.find("select").length) {
        data[field] = $cell.find("select").val();
      } else if ($cell.find("input").length) {
        data[field] = $cell.find("input").val();
      } else {
        data[field] = $cell.text().trim();
      }
    });
    return data;
  }

  // Store original data before editing (for cancel)
  function getOriginalData($row) {
    let data = {};
    $row.find(".editable-cell").each(function () {
      const $cell = $(this);
      const field = $cell.data("field");
      data[field] = $cell.text().trim();
      if (field === "is_superuser" || field === "is_staff") {
        data[field] = data[field] === "Yes" ? true : false;
      }
    });
    return data;
  }


  $('#employee-search').on('keyup', function() {
    var searchTerm = $(this).val().toLowerCase().trim();

    $('#employee-table tbody tr').each(function() {
      // Get employee name cell text
      var employeeName = $(this).find('td[data-field="employee_name"]').text().toLowerCase().trim();

      // Show row if employee name contains search term, else hide
      if (employeeName.indexOf(searchTerm) !== -1) {
        $(this).show();
      } else {
        $(this).hide();
      }
    });
  });


  $('#client-search').on('keyup', function() {
  var searchTerm = $(this).val().toLowerCase().trim();

  $('#client-table tbody tr').each(function() {
      var clientName = $(this).find('td[data-field="client_name"]').text().toLowerCase().trim();
      if (clientName.indexOf(searchTerm) !== -1) {
        $(this).show();
      } else {
        $(this).hide();
      }
    });
  });

  // Users search filter
  $('#users-search').on('keyup', function() {
    var searchTerm = $(this).val().toLowerCase().trim();

  $('#users-table tbody tr').each(function() {
      var username = $(this).find('td[data-field="first_name"]').text().toLowerCase().trim();
      if (username.indexOf(searchTerm) !== -1) {
        $(this).show();
      } else {
        $(this).hide();
      }
    });
  });




  // Add New button click: add new row with inputs and 'new' data-id
  $("button[id$='-add-btn'], #add-new-employee").click(function () {
    const tableId = $(this).closest(".tab-pane").find("table").attr("id");
    const $tableBody = $("#" + tableId + " tbody");

    // Columns count excluding Actions column
    const columnsCount = $("#" + tableId + " thead tr th").length - 1;

    // Create new row with empty input cells and "new" data-id
    let $newRow = $('<tr data-id="new"></tr>');

    // Add ID cell (empty for new)
    $newRow.append('<td class="static-cell"></td>');

    // Add editable cells with input fields
    for (let i = 1; i < columnsCount; i++) {
      // Get field name from header or fallback
      const field = $("#" + tableId + " thead tr th").eq(i).text().trim().toLowerCase().replace(/\s/g, '_');


      // Use input or select for boolean columns
      if (field === "is_superuser" || field === "is_staff") {
        $newRow.append(`<td class="editable-cell" data-field="${field}">
          <select class="form-control form-control-sm">
            <option value="No" selected>No</option>
            <option value="Yes">Yes</option>
          </select>
        </td>`);
      } else {
        $newRow.append(`<td class="editable-cell" data-field="${field}"><input type="text" class="form-control form-control-sm" value=""></td>`);
      }
    }

    // Actions cell with Save and Cancel buttons shown initially for new row
    $newRow.append(`
      <td>
        <button class="btn btn-success btn-sm btn-save" title="Save"><i class="fas fa-save"></i></button>
        <button class="btn btn-secondary btn-sm btn-cancel" title="Cancel"><i class="fas fa-times"></i></button>
        <button class="btn btn-primary btn-sm btn-edit" title="Edit" style="display:none;"><i class="fas fa-edit"></i></button>
        <button class="btn btn-danger btn-sm btn-delete" title="Delete" style="display:none;"><i class="fas fa-trash"></i></button>
      </td>
    `);

    $tableBody.prepend($newRow);
  });

  // Edit button click: switch row to edit mode
  $("body").on("click", ".btn-edit", function () {
    const $row = $(this).closest("tr");
    $row.data("originalData", getOriginalData($row)); // Save original data for cancel
    switchToEdit($row);
  });

  // Cancel button click: revert row to view mode
  $("body").on("click", ".btn-cancel", function () {
    const $row = $(this).closest("tr");
    if ($row.attr("data-id") === "new") {
      // If new row, remove it on cancel
      $row.remove();
    } else {
      // Else revert to original data
      switchToView($row, $row.data("originalData"));
    }
  });

  // Save button click: send AJAX to create or update
  $("body").on("click", ".btn-save", function () {
    const $row = $(this).closest("tr");
    const isNew = $row.attr("data-id") === "new";
    const tableId = $row.closest("table").attr("id");

    let postData = {};

    if (tableId === "employee-table") {
      // Explicitly get each field value from inputs/selects
      postData = {
        employee_name: $row.find("td[data-field='employee_name'] input").val() || '',
        audit_manager: $row.find("td[data-field='audit_manager'] input").val() || '',
        partner: $row.find("td[data-field='partner'] input").val() || '',
        admin: $row.find("td[data-field='admin'] input").val() || '',
      };
      if (!isNew) {
        postData.id = $row.attr("data-id");
      }
    } else {
      // For other tables, keep your current dynamic collection
      postData = collectRowData($row);
      if (!isNew) {
        postData["id"] = $row.attr("data-id");
      }
    }

    const urlMap = {
      "employee-table": isNew ? "/save-employee/" : "/update-employee/",
      "client-table": isNew ? "/save-client/" : "/update-client/",
      "users-table": isNew ? "/save-user/" : "/update-user/"
    };

    $.ajax({
      url: urlMap[tableId],
      method: "POST",
      headers: { "X-CSRFToken": getCSRFToken() },
      data: postData,
      success: function (response) {
        if (isNew) {
          $row.attr("data-id", response.id);
          $row.find("td:first").text(response.id);
          $row.find(".btn-edit, .btn-delete").show();
          $row.find(".btn-save, .btn-cancel").hide();
        }
        switchToView($row);
      },
      error: function () {
        alert("Error saving data. Please try again.");
      }
    });
  });


  // Delete button click: confirm and send AJAX to delete
  $("body").on("click", ".btn-delete", function () {
    if (!confirm("Are you sure you want to delete this record?")) return;

    const $row = $(this).closest("tr");
    const id = $row.attr("data-id");
    const tableId = $row.closest("table").attr("id");

    if (id === "new") {
      $row.remove(); // Just remove new unsaved row
      return;
    }

    const urlMap = {
      "employee-table": "/delete-employee/",
      "client-table": "/delete-client/",
      "users-table": "/delete-user/"
    };

    $.ajax({
      url: urlMap[tableId],
      method: "POST",
      headers: { "X-CSRFToken": getCSRFToken() },
      data: { id: id },
      success: function () {
        $row.remove();
      },
      error: function () {
        alert("Error deleting data. Please try again.");
      }
    });
  });

});
