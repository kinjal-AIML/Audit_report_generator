
document.addEventListener("DOMContentLoaded", function () {


    
  function loadAllocatedData() {
    const fromDate = document.getElementById("fromDate").value;
    const toDate = document.getElementById("toDate").value;

    if (!fromDate || !toDate) {
      alert("Please select both From and To dates.");
      return;
    }

    fetch(`/allocated_data?fromDate=${fromDate}&toDate=${toDate}`)
      .then(response => response.json())
      .then(data => {
        const tableHead = document.querySelector("#allocatedTable thead tr");
        const tableBody = document.getElementById("tableBody");

        tableHead.innerHTML = "";
        tableBody.innerHTML = "";

        // Render headers
        let headers = "";
        data.col_display.forEach(colName => {
          if (colName.toLowerCase() === "date" || colName.toLowerCase() === "day") {
            headers += `<th>${colName.toUpperCase()}</th>`;
          } else {
            headers += `<th>${colName}</th>`;
          }
        });
        tableHead.innerHTML = headers;

        // Render rows
        data.rows.forEach(row => {
            // Find the day cell value (case-insensitive check)
            const dayValRaw = row["Day"] || row["day"] || ""; 
            const dayVal = dayValRaw.toString().slice(0,3).toLowerCase(); // e.g. "sun"

            // Add highlight class if day is "sun"
            const trClass = dayVal === "sun" ? 'class="highlight-sun"' : '';

            let tr = `<tr ${trClass}>`;
            data.columns.forEach(col => {
                let cellData = row[col] || "";

                // Format date column to DD-MM-YYYY
                if (col.toLowerCase() === "date" && cellData) {
                const dateObj = new Date(cellData);
                if (!isNaN(dateObj)) {
                    const day = String(dateObj.getDate()).padStart(2, '0');
                    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
                    const year = dateObj.getFullYear();
                    cellData = `${day}-${month}-${year}`;
                }
                }

                // Format day to short (Sun, Mon, ...)
                if (col.toLowerCase() === "day" && cellData) {
                const shortDay = cellData.slice(0, 3);
                cellData = shortDay.charAt(0).toUpperCase() + shortDay.slice(1).toLowerCase();
                }

                tr += `<td>${cellData}</td>`;
            });
            tr += "</tr>";
            tableBody.innerHTML += tr;
            });


        adjustColumnWidths("#allocatedTable");
      })
      .catch(error => {
        console.error("Error loading allocated data:", error);
        alert("Failed to load data.");
      });
  }

  function adjustColumnWidths(tableSelector) {
    const table = document.querySelector(tableSelector);
    if (!table) return;

    const rows = table.rows;
    if (rows.length === 0) return;

    const colCount = rows[0].cells.length;
    const maxCharLengths = new Array(colCount).fill(0);

    for (let r = 0; r < rows.length; r++) {
        const cells = rows[r].cells;
        for (let c = 0; c < colCount; c++) {
        if (!cells[c]) continue;
        const text = (cells[c].innerText || cells[c].textContent || "").trim();
        if (text.length > maxCharLengths[c]) {
            maxCharLengths[c] = text.length;
        }
        }
    }

    const approxCharWidth = 8;
    let leftOffset = 0;
    for (let c = 0; c < colCount; c++) {
        let colWidth = maxCharLengths[c] * approxCharWidth + 20;

        if (c === 0 && colWidth < 120) colWidth = 120;
        if (c === 1 && colWidth < 100) colWidth = 100;

        for (let r = 0; r < rows.length; r++) {
            if (!rows[r].cells[c]) continue;
            const cell = rows[r].cells[c];

            if (rows[r].classList.contains("highlight-sun")) {
                cell.style.backgroundColor = "#F08080 ";
            } else {
                cell.style.backgroundColor = "";
            }

            cell.style.minWidth = colWidth + "px";
            cell.style.overflow = "hidden";
            cell.style.textOverflow = "ellipsis";
            cell.style.whiteSpace = "nowrap";

            if (c === 0 || c === 1) {
                cell.style.position = "sticky";
                cell.style.left = leftOffset + "px";
                cell.style.zIndex = c === 0 ? 25 : 24;
                cell.style.boxShadow = "2px 0 5px -2px rgba(0,0,0,0.15)";
            }
        }


        if (c === 0 || c === 1) {
        leftOffset += colWidth;
        }
    }
    }


  function addRowClickSelection() {
    const tableBody = document.querySelector("#allocatedTable tbody");
    tableBody.addEventListener("click", function(event) {
        const clickedRow = event.target.closest("tr");
        if (!clickedRow) return;

        // Remove 'selected' class from all rows
        tableBody.querySelectorAll("tr").forEach(row => {
        row.classList.remove("selected");
        });

        // Add 'selected' class to clicked row
        clickedRow.classList.add("selected");
    });
    }

    adjustColumnWidths("#allocatedTable");

    addRowClickSelection();  // <<< **Add this here!**


    // Auto-load when dates change
    const fromInput = document.getElementById("fromDate");
    const toInput = document.getElementById("toDate");

    function tryLoadData() {
        if (fromInput.value && toInput.value) {
        loadAllocatedData();
        }
    }

    fromInput.addEventListener("change", tryLoadData);
    toInput.addEventListener("change", tryLoadData);


    // document.getElementById("exportExcel").addEventListener("click", function () {
    //     const table = document.getElementById("allocatedTable");
    //     const workbook = XLSX.utils.table_to_book(table, { sheet: "AllocatedData" });
    //     XLSX.writeFile(workbook, "allocated_data.xlsx");
    // });

    document.getElementById("exportExcel").addEventListener("click", function () {
        const fromDate = document.getElementById("fromDate").value;
        const toDate = document.getElementById("toDate").value;

        if (!fromDate || !toDate) {
            alert("Please select both From and To dates.");
            return;
        }

        // Construct URL with query params
        const url = `/export-allocated-data/?fromDate=${fromDate}&toDate=${toDate}`;

        // Trigger file download by opening URL in new tab/window
        window.open(url, '_blank');
    });


});

