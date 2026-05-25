document.addEventListener("DOMContentLoaded", () => {
  
  // Monthly Spend vs. Usage/Bill Count (Horizontal Stacked Bar Chart)
  const billingLabels = JSON.parse(document.getElementById("monthlySpendLabels").textContent);
  const monthlySpendData = JSON.parse(document.getElementById("monthlySpendData").textContent);
  const billCountData = JSON.parse(document.getElementById("billCountData").textContent); // Assuming this data is available
  
  new Chart(document.getElementById("billingChart"), {
    type: "bar", // Horizontal Bar chart
    data: {
      labels: billingLabels,
      datasets: [
        {
          label: "Monthly Spend (₹)",
          data: monthlySpendData,
          backgroundColor: "#3b82f6",
          stack: "stack1",
        },
        {
          label: "Bill Count",
          data: billCountData,
          backgroundColor: "#e74c3c",
          stack: "stack1",
        },
      ],
    },
    options: {
      responsive: true,
      indexAxis: "y", // This makes it horizontal
      scales: {
        x: {
          stacked: true, // Stack the bars horizontally
        },
        y: {
          stacked: true, // Stack the bars vertically
        },
      },
      plugins: {
        legend: { position: "top" }, // Legend on top
      },
    },
  });

  // Utility Spend Breakdown (Polar Area Chart)
  const utilityLabels = JSON.parse(document.getElementById("utilitySpendLabels").textContent);
  const utilityData = JSON.parse(document.getElementById("utilitySpendData").textContent);
  
  new Chart(document.getElementById("utilitySpendChart"), {
    type: "polarArea", // Polar Area Chart
    data: {
      labels: utilityLabels,
      datasets: [{
        label: "Proportional Utility Spend",
        data: utilityData,
        backgroundColor: ["#10b981", "#ef4444", "#6366f1", "#f59e0b", "#3b82f6"],
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom", // Position the legend at the bottom
        },
      },
    },
  });

  // Spike Chart (Line/Area Chart - Highlight sudden spikes)
  const spikeLabels = JSON.parse(document.getElementById("monthlySpendLabels").textContent);
  const spikeData = JSON.parse(document.getElementById("monthlySpendData").textContent); // Assuming spend data has spikes
  
  new Chart(document.getElementById("spikeChart"), {
    type: "line", // Line chart
    data: {
      labels: spikeLabels,
      datasets: [{
        label: "Monthly Spend (₹)",
        data: spikeData,
        borderColor: "#ff6347", // Color for the line
        backgroundColor: "rgba(255, 99, 71, 0.2)", // Light red fill
        fill: true,
        tension: 0.4, // Curve the line
      }],
    },
    options: {
      responsive: true,
      scales: {
        x: {
          title: {
            display: true,
            text: "Month", // Label for X-axis
          },
        },
        y: {
          title: {
            display: true,
            text: "Spend (₹)", // Label for Y-axis
          },
          beginAtZero: true, // Start the Y-axis from zero
        },
      },
    },
  });

  // Payment Discipline Trend (Line Chart - Track early/late payments)
  const paymentLabels = JSON.parse(document.getElementById("paymentDisciplineLabels").textContent);
  const paymentData = JSON.parse(document.getElementById("paymentDisciplineData").textContent); // Assuming this data exists (early/late days)
  
  new Chart(document.getElementById("paymentDisciplineTrend"), {
    type: "line", // Line chart
    data: {
      labels: paymentLabels,
      datasets: [{
        label: "Days Early/Late",
        data: paymentData,
        borderColor: "#34d399", // Green for early payments
        backgroundColor: "rgba(52, 211, 153, 0.2)", // Light green fill
        fill: true,
        tension: 0.3, // Line curve tension
      }],
    },
    options: {
      responsive: true,
      scales: {
        x: {
          title: {
            display: true,
            text: "Month", // Label for X-axis
          },
        },
        y: {
          title: {
            display: true,
            text: "Days (Early/Late)", // Label for Y-axis
          },
          suggestedMin: -5, // Suggested range for early payments (negative)
          suggestedMax: 5,  // Suggested range for late payments (positive)
        },
      },
    },
  });
});
