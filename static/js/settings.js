document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("settingsForm");

  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const reminderDays = document.getElementById("reminder_days").value;
    const notificationMethod = document.getElementById("notification_method").value;
    const timezone = document.getElementById("timezone").value;

    const settingsData = {
      reminder_days: parseInt(reminderDays),
      notification_method: notificationMethod,
      timezone: timezone,
    };

    console.log("Settings submitted:", settingsData);

    // Replace with AJAX call or fetch request to save settings
    alert("Settings saved successfully!");
  });
});
