async function generateReport() {

    const file = document.getElementById('reportFile').files[0];
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    const formData = new FormData();

    formData.append('file', file);
    formData.append('start_date', startDate);
    formData.append('end_date', endDate);

    document.getElementById('status').innerText = 'Generating report...';

    const response = await fetch(
        'http://127.0.0.1:8000/generate-report',
        {
            method: 'POST',
            body: formData
        }
    );

    const data = await response.json();

    document.getElementById('status').innerText = data.message;

    const downloadBtn = document.getElementById('downloadBtn');

    downloadBtn.href = `http://127.0.0.1:8000${data.download_url}`;

    downloadBtn.style.display = 'block';
}