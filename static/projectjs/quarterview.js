document.addEventListener('DOMContentLoaded', function () {
  const employeeList = document.getElementById('employeeList');
  const employeeSearch = document.getElementById('employeeSearch');

  let selectedEmployee = null;

  employeeList.addEventListener('click', function (e) {
    if (e.target && e.target.matches('li.list-group-item')) {
      if (e.target.classList.contains('selected')) {
        e.target.classList.remove('selected');
        selectedEmployee = null;
        generateGrid();
      } else {
        const prevSelected = employeeList.querySelector('.selected');
        if (prevSelected) prevSelected.classList.remove('selected');
        e.target.classList.add('selected');
        selectedEmployee = e.target.textContent.trim();
        generateGrid();
      }
    }
  });

  employeeSearch.addEventListener('input', function () {
    const filter = this.value.toLowerCase();
    const items = employeeList.getElementsByTagName('li');
    Array.from(items).forEach(item => {
      const text = item.textContent.toLowerCase();
      item.style.display = text.includes(filter) ? '' : 'none';
    });
  });

  function getMonthHeaders(fromDateStr, toDateStr) {
    const fromDate = new Date(fromDateStr);
    const toDate = new Date(toDateStr);
    let months = [];

    let current = new Date(fromDate.getFullYear(), fromDate.getMonth(), 1);

    while (current <= toDate && months.length < 3) {
      months.push(current.toLocaleString('default', { month: 'long' }));
      current.setMonth(current.getMonth() + 1);
    }

    while (months.length < 3) {
      months.push('');
    }

    return months;
  }

  function formatDateDDMMYYYY(date) {
    const dd = String(date.getDate()).padStart(2, '0');
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const yyyy = date.getFullYear();
    return `${dd}-${mm}-${yyyy}`;
    }


  function formatDateYYYYMMDD(date) {
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  }

  function setDefaultDateRange() {
    const fromDateInput = document.getElementById('fromDate');
    const toDateInput = document.getElementById('toDate');
    if (!fromDateInput || !toDateInput) return;

    const now = new Date();

    const firstDayCurrentMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDayThirdMonth = new Date(now.getFullYear(), now.getMonth() + 3, 0);

    fromDateInput.value = formatDateYYYYMMDD(firstDayCurrentMonth);
    toDateInput.value = formatDateYYYYMMDD(lastDayThirdMonth);
  }

  let planningData = {}; // { 'DD-MM-YYYY': [event1, event2, ...], ... }

  async function fetchPlanningData(employeeName, fromDate, toDate) {
    if (!employeeName) {
      planningData = {};
      return;
    }
    try {
      const url = new URL('/api/get_planning_data/', window.location.origin);
      url.searchParams.append('employee_name', employeeName);
      url.searchParams.append('from_date', fromDate);
      url.searchParams.append('to_date', toDate);

      const response = await fetch(url);
      if (!response.ok) {
        console.error('Error fetching planning data', response.status);
        planningData = {};
        return;
      }

      planningData = await response.json();
    } catch (error) {
      console.error('Fetch error:', error);
      planningData = {};
    }
  }

  async function generateGrid() {
    const gridContainer = document.getElementById('gridContainer');
    if (!gridContainer) return;

    gridContainer.innerHTML = '';

    const fromDateInput = document.getElementById('fromDate');
    const toDateInput = document.getElementById('toDate');

    if (!fromDateInput.value || !toDateInput.value) return;

    let fromDate = new Date(fromDateInput.value);
    let toDate = new Date(toDateInput.value);

    if (fromDate > toDate) {
      [fromDate, toDate] = [toDate, fromDate];
    }

    const monthHeaders = getMonthHeaders(fromDateInput.value, toDateInput.value);

    // ONLY 4 columns: Date + 3 months
    const headers = ['Date', ...monthHeaders];
    headers.forEach(header => {
      const headerCell = document.createElement('div');
      headerCell.classList.add('grid-cell', 'header-cell');
      headerCell.textContent = header;
      gridContainer.appendChild(headerCell);
    });

    // Fetch planning data before building rows
    await fetchPlanningData(
      selectedEmployee,
      formatDateYYYYMMDD(fromDate),
      formatDateYYYYMMDD(toDate)
    );

    // Max days = 31
    for (let day = 1; day <= 31; day++) {
      // Column 1: Date (day number)
      const dateCell = document.createElement('div');
      dateCell.classList.add('grid-cell', 'date-cell');
      dateCell.textContent = day;
      dateCell.dataset.row = day;  // Add data-row attribute

      // Add hover event to highlight row
      dateCell.addEventListener('mouseenter', () => highlightRow(day, true));
      dateCell.addEventListener('mouseleave', () => highlightRow(day, false));

      gridContainer.appendChild(dateCell);

      // Columns 2,3,4: Each month data with weekday + events
      for (let i = 0; i < 3; i++) {
        const monthName = monthHeaders[i];
        if (!monthName) {
          const emptyCell = document.createElement('div');
          emptyCell.classList.add('grid-cell');
          emptyCell.dataset.row = day; // Add data-row attribute
          emptyCell.addEventListener('mouseenter', () => highlightRow(day, true));
          emptyCell.addEventListener('mouseleave', () => highlightRow(day, false));
          gridContainer.appendChild(emptyCell);
          continue;
        }

        const baseYear = fromDate.getFullYear();
        const baseMonth = fromDate.getMonth();
        const cellDate = new Date(baseYear, baseMonth + i, day);

        // Skip invalid dates (like Feb 30)
        if (cellDate.getDate() !== day) {
          const emptyCell = document.createElement('div');
          emptyCell.classList.add('grid-cell');
          emptyCell.dataset.row = day;
          emptyCell.addEventListener('mouseenter', () => highlightRow(day, true));
          emptyCell.addEventListener('mouseleave', () => highlightRow(day, false));
          gridContainer.appendChild(emptyCell);
          continue;
        }

        const dayShort = cellDate.toLocaleString('default', { weekday: 'short' });
        const dateKey = formatDateDDMMYYYY(cellDate);
        const events = planningData[dateKey] ? planningData[dateKey].join(', ') : '';

        const cell = document.createElement('div');
        cell.classList.add('grid-cell', 'planning-cell');

        if (dayShort === 'Sun') {
          cell.classList.add('sunday-cell');
        }

        if (events.toLowerCase().includes('holiday')) {
          cell.classList.add('holiday-cell');
        } else if (events.toLowerCase().includes('leave')) {
          cell.classList.add('leave-cell');
        }

        const daySpan = document.createElement('span');
        daySpan.classList.add('day-name');
        daySpan.textContent = dayShort;

        const eventSpan = document.createElement('span');
        eventSpan.classList.add('event-text');
        eventSpan.textContent = events;

        cell.appendChild(daySpan);
        cell.appendChild(eventSpan);
        cell.dataset.row = day;  // Add data-row attribute

        // Add hover event to highlight row
        cell.addEventListener('mouseenter', () => highlightRow(day, true));
        cell.addEventListener('mouseleave', () => highlightRow(day, false));

        gridContainer.appendChild(cell);
      }
    }
  }

  // Helper function to highlight all cells of a row
  function highlightRow(rowNumber, highlight) {
    const gridContainer = document.getElementById('gridContainer');
    if (!gridContainer) return;

    const cells = gridContainer.querySelectorAll(`[data-row='${rowNumber}']`);
    cells.forEach(cell => {
      if (highlight) {
        cell.classList.add('row-highlight');
      } else {
        cell.classList.remove('row-highlight');
      }
    });
  }


  setDefaultDateRange();
  generateGrid();

  document.getElementById('fromDate').addEventListener('change', generateGrid);
  document.getElementById('toDate').addEventListener('change', generateGrid);



  document.getElementById('exportExcel').addEventListener('click', function () {
    const fromDate = document.getElementById('fromDate').value;
    const toDate = document.getElementById('toDate').value;
    const selectedEmployeeElem = document.querySelector('#employeeList li.selected');
    const employeeName = selectedEmployeeElem ? selectedEmployeeElem.textContent.trim() : null;

    if (!fromDate || !toDate) {
        alert('Please select From Date and To Date');
        return;
    }

    if (!employeeName) {
        alert('Please select an employee before exporting.');
        return;
    }

    let url = new URL('/quarterview_excel/', window.location.origin);
    url.searchParams.append('from_date', fromDate);
    url.searchParams.append('to_date', toDate);
    url.searchParams.append('employee_name', employeeName);

    // Open the URL in a new tab to trigger download
    window.open(url.toString(), '_blank');
    });


  document.getElementById('exportPDF').addEventListener('click', function () {
    const fromDate = document.getElementById('fromDate').value;
    const toDate = document.getElementById('toDate').value;
    const selectedEmployeeElem = document.querySelector('#employeeList li.selected');
    const employeeName = selectedEmployeeElem ? selectedEmployeeElem.textContent.trim() : null;

    if (!fromDate || !toDate) {
        alert('Please select From Date and To Date');
        return;
    }

    if (!employeeName) {
        alert('Please select an employee before exporting.');
        return;
    }

    let url = new URL('/quarterview_pdf/', window.location.origin);
    url.searchParams.append('from_date', fromDate);
    url.searchParams.append('to_date', toDate);
    url.searchParams.append('employee_name', employeeName);

    // Open the URL in a new tab to trigger download
    window.open(url.toString(), '_blank');
    });


});
