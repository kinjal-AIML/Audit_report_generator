document.addEventListener('DOMContentLoaded', function () {
  const calendarEl = document.getElementById('calendar');
  const monthSelect = document.getElementById('calendar-month');
  const yearSelect = document.getElementById('calendar-year');
  const employeeList = document.getElementById('employeeList');
  const employeeSearch = document.getElementById('employeeSearch');

  let selectedEmployee = null;
  let selectedEventClients = [];


  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const today = new Date();
  const currentYear = today.getFullYear();

  // Populate month/year dropdowns
  for (let m = 0; m < 12; m++) {
    const opt = new Option(monthNames[m], m);
    monthSelect.appendChild(opt);
  }

  for (let y = currentYear - 10; y <= currentYear + 50; y++) {
    const opt = new Option(y, y);
    yearSelect.appendChild(opt);
  }

  // Set default values
  monthSelect.value = today.getMonth();
  yearSelect.value = today.getFullYear();

  // Initialize FullCalendar
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    height: '100%',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay,listMonth'
    },
    nowIndicator: true,
    selectable: true,
    navLinks: true,
    dayMaxEvents: false,
    showNonCurrentDates: true,
    firstDay: 1,

    eventDidMount: function(info) {
      info.el.style.color = 'black';
      info.el.style.fontWeight = 'bold';
      // In case event element has child nodes, set them too
      Array.from(info.el.querySelectorAll('*')).forEach(el => {
        el.style.color = 'black';
        el.style.fontWeight = 'bold';
      });
    },

    eventClick: function(info) {
      const event = info.event;

      if (!selectedEmployee) {
        alert('Please select an employee first.');
        return;
      }

      // Fill modal fields with event data
      document.getElementById('fromDate').value = event.startStr;
      document.getElementById('toDate').value = event.endStr ? event.endStr.slice(0,10) : event.startStr;

      // Set dayType (from extendedProps if available)
      document.getElementById('dayType').value = event.extendedProps.day_type || 'full day';

      // Clear all previous client selections
      const categorySelect = document.getElementById('category');
      Array.from(categorySelect.options).forEach(opt => opt.selected = false);

      // Select clients from event.extendedProps.clients (array)
      const clients = event.extendedProps.clients || [];
      clients.forEach(client => {
        for (const option of categorySelect.options) {
          if (option.value === client) {
            option.selected = true;
            break;
          }
        }
      });

    

      // Fill description
      document.getElementById('description').value = event.extendedProps.description || '';

      // Show modal
      const modal = new bootstrap.Modal(document.getElementById('eventModal'));
      modal.show();

      // Save event ID to modal for save/delete actions
      document.getElementById('eventModal').dataset.eventId = event.id;
    },

    

    dateClick: function (info) {
      if (!selectedEmployee) {
        alert('Please select an employee first.');
        return; // Don't open modal
      }
      const dateStr = info.dateStr;
      document.getElementById('fromDate').value = dateStr;
      document.getElementById('toDate').value = dateStr;
      document.getElementById('dayType').value = 'full day';
      document.getElementById('category').selectedIndex = -1;
      document.getElementById('description').value = ''; // Clear the old description

      const modal = new bootstrap.Modal(document.getElementById('eventModal'));
      modal.show();
    },

    datesSet: function () {
      const currentDate = calendar.getDate();  // Correct center date
      monthSelect.value = currentDate.getMonth();
      yearSelect.value = currentDate.getFullYear();

      document.querySelectorAll('.fc-daygrid-day.fc-day-sun').forEach(cell => {
        cell.style.backgroundColor = '#f2e9d0';
      });

      if (selectedEmployee) {
        const month = currentDate.getMonth() + 1; // 0-indexed
        const year = currentDate.getFullYear();
        fetchAndShowEvents(selectedEmployee, month, year);
        fetchAndUpdateSummary(selectedEmployee, month, year);
      }
    }
  });

  calendar.render();

  
  
  document.querySelectorAll('[data-widget="pushmenu"]').forEach(toggleBtn => {
    toggleBtn.addEventListener('click', () => {
      setTimeout(() => {
        calendar.updateSize();
      }, 300);  // delay to let sidebar animation finish
    });
  });

  

  // Fetch & render planning data as calendar events
  function fetchAndShowEvents(employeeName, month, year) {
    const url = `/api/get-events/?employee_name=${encodeURIComponent(employeeName)}&month=${month}&year=${year}`;

    fetch(url)
      .then(response => response.json())
      .then(events => {
        calendar.removeAllEvents();  // Clear old events
        events.forEach(event => {
          calendar.addEvent({
            id: event.id,  // unique ID from your backend event object
            title: event.title || '',  // or whatever your event title is
            start: event.start,
            end: event.end,
            color: event.color,
            extendedProps: {
              day_type: event.day_type,
              clients: event.clients,  // array of client names/IDs for that event
              description: event.description,
            },
          });
        });

      })
      .catch(error => {
        console.error("Error fetching events:", error);
      });
  }

  // Dropdown month/year selection updates calendar view
  function updateCalendarFromDropdown() {
    const month = parseInt(monthSelect.value);
    const year = parseInt(yearSelect.value);
    const newDate = new Date(year, month, 1);
    calendar.gotoDate(newDate);

    if (selectedEmployee) {
      const oneBasedMonth = month + 1;
      fetchAndShowEvents(selectedEmployee, oneBasedMonth, year);
      fetchAndUpdateSummary(selectedEmployee, oneBasedMonth, year);
    } else {
      updateSummaryCounts(0,0,0,0,0,0);
    }
  }

  monthSelect.addEventListener('change', updateCalendarFromDropdown);
  yearSelect.addEventListener('change', updateCalendarFromDropdown);

  // Employee selection
  employeeList.addEventListener('click', function (e) {
    if (e.target && e.target.matches('li.list-group-item')) {
      const previouslySelected = employeeList.querySelector('.selected');
      if (previouslySelected && previouslySelected !== e.target) {
        previouslySelected.classList.remove('selected');
      }
      e.target.classList.toggle('selected');

      if (e.target.classList.contains('selected')) {
        selectedEmployee = e.target.textContent.trim();
        const selectedMonth = parseInt(monthSelect.value) + 1; // JS 0-indexed
        const selectedYear = parseInt(yearSelect.value);

        fetchAndShowEvents(selectedEmployee, selectedMonth, selectedYear);
        fetchAndUpdateSummary(selectedEmployee, selectedMonth, selectedYear);
      } else {
        selectedEmployee = null;
        calendar.removeAllEvents();
        updateSummaryCounts(0,0,0,0,0,0);
      }
    }
  });

  // Search filter for employees
  employeeSearch.addEventListener('input', function () {
    const filter = this.value.toLowerCase();
    const items = employeeList.getElementsByTagName('li');

    Array.from(items).forEach(function (item) {
      const text = item.textContent.toLowerCase();
      item.style.display = text.includes(filter) ? '' : 'none';
    });
  });

  // Responsive resize
  const observer = new MutationObserver(mutations => {
    mutations.forEach(mutation => {
      if (mutation.attributeName === 'class') {
        calendar.updateSize();
      }
    });
  });

  observer.observe(document.body, { attributes: true });
  window.addEventListener('resize', () => calendar.updateSize());



  // ---------------- Save Button ----------------

  document.getElementById('saveEvent').addEventListener('click', function (e) {
    e.preventDefault();

    if (!selectedEmployee) {
      alert('Please select an employee before saving.');
      return;
    }

    const fromDate = document.getElementById('fromDate').value;
    const toDate = document.getElementById('toDate').value;
    const dayType = document.getElementById('dayType').value;

    const categorySelect = document.getElementById('category');
    const selectedClients = Array.from(categorySelect.selectedOptions).map(opt => opt.value);
    const description = document.getElementById('description').value;

    if (!fromDate || !toDate) {
      alert('Please select valid From and To dates.');
      return;
    }

    if (selectedClients.length === 0) {
      alert('Please select at least one category or client.');
      return;
    }

    
    // Get existing event ID from modal data (set during eventClick)
    const eventId = document.getElementById('eventModal').dataset.eventId || null;

    const postData = {
      event_id: eventId,  // Pass to backend: null for new, or ID to update
      employee_name: selectedEmployee,
      from_date: fromDate,
      to_date: toDate,
      day_type: dayType,
      clients: selectedClients,
      description: description,
    };

    // --- Save button fetch call (update URL if needed) ---
    fetch('/save-planning/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify(postData),
    })
      .then(async response => {
      const data = await response.json();  // parse JSON response first

      if (!response.ok) {
        // If backend returned error status, show its error message
        throw new Error(data.error || 'Unknown error');
      }

        return data;
      })
      .then(data => {
        alert(data.message || 'Planning saved successfully.');
        $('#eventModal').modal('hide');

        // Clear modal fields
        document.getElementById('description').value = '';
        document.getElementById('eventModal').dataset.eventId = ''; // reset for new event

        // Refresh calendar events for current selection
        const selectedMonth = parseInt(monthSelect.value) + 1;
        const selectedYear = parseInt(yearSelect.value);
        fetchAndShowEvents(selectedEmployee, selectedMonth, selectedYear);
        fetchAndUpdateSummary(selectedEmployee, selectedMonth, selectedYear);
      })
      .catch(error => {
        alert('Error saving planning: ' + error.message);
      });
  });


  // ---------------- Delete Button ----------------
  document.getElementById('deleteEvent').addEventListener('click', function (e) {
    e.preventDefault();

    if (!selectedEmployee) {
      alert('Please select an employee before deleting.');
      return;
    }


    const fromDate = document.getElementById('fromDate').value;
    const toDate = document.getElementById('toDate').value;

    if (!fromDate || !toDate) {
      alert('Please select valid From and To dates.');
      return;
    }

    const categorySelect = document.getElementById('category');
    const selectedClients = Array.from(categorySelect.selectedOptions).map(opt => opt.value);
    

    const fromFormatted = new Date(fromDate).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    });

    const toFormatted = new Date(toDate).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    });

    if (!confirm(`Are you sure you want to delete planning from ${fromFormatted} to ${toFormatted} for ${selectedEmployee}?`)) {
      return;
    }


    

    fetch('/delete-planning/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({
        employee_name: selectedEmployee,
        from_date: fromDate,
        to_date: toDate,
        clients: selectedClients  // 👈 include selected clients
        
      }),
    })
    
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        alert(data.message || 'Planning deleted successfully.');
        $('#eventModal').modal('hide');

        // Refresh calendar events
        const selectedMonth = parseInt(monthSelect.value) + 1;
        const selectedYear = parseInt(yearSelect.value);
        fetchAndShowEvents(selectedEmployee, selectedMonth, selectedYear);
        fetchAndUpdateSummary(selectedEmployee, selectedMonth, selectedYear);
      })
      .catch(error => {
        alert('Error deleting planning: ' + error.message);
      });
  });


  document.getElementById('exportExcel').addEventListener('click', function () {
    if (!selectedEmployee) {
      alert("Please select an employee before exporting.");
      return;
    }

    const month = parseInt(monthSelect.value) + 1; // JS is 0-based
    const year = parseInt(yearSelect.value);

    const url = `/export-planning-excel/?employee_name=${encodeURIComponent(selectedEmployee)}&month=${month}&year=${year}`;

    // Trigger file download
    window.location.href = url;
  });

  document.getElementById('exportPDF').addEventListener('click', function () {
    if (!selectedEmployee) {
      alert("Please select an employee before exporting.");
      return;
    }

    const month = parseInt(monthSelect.value) + 1;
    const year = parseInt(yearSelect.value);

    const url = `/export-planning-pdf/?employee_name=${encodeURIComponent(selectedEmployee)}&month=${month}&year=${year}`;
    window.location.href = url;
  });



  function fetchAndUpdateSummary(employeeName, month, year) {
    if (!employeeName) {
      // Clear counts if no employee selected
      updateSummaryCounts(0,0,0,0,0,0);
      return;
    }

    const url = `/api/get-planning-summary/?employee_name=${encodeURIComponent(employeeName)}&month=${month}&year=${year}`;

    fetch(url)
      .then(response => response.json())
      .then(data => {
        updateSummaryCounts(
          data.working_days,
          data.available,
          data.allocated,
          data.pending,
          data.holiday,
          data.leave
        );
      })
      .catch(error => {
        console.error('Error fetching summary:', error);
        updateSummaryCounts(0,0,0,0,0,0);
      });
  }

function updateSummaryCounts(working, available, allocated, pending, holiday, leave) {
  document.getElementById('workingDaysCount').textContent = working;
  document.getElementById('availableCount').textContent = available;
  document.getElementById('allocatedCount').textContent = allocated;
  document.getElementById('pendingCount').textContent = pending;
  document.getElementById('holidayCount').textContent = holiday;
  document.getElementById('leaveCount').textContent = leave;
}


  // ---------------- Helper: Get CSRF Token ----------------
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  
  

});
