const form = document.getElementById('job-form');
const jobIdEl = document.getElementById('job-id');
const statusEl = document.getElementById('status');
const resultEl = document.getElementById('result');

let pollTimer = null;

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function fetchJob(jobId) {
  const response = await fetch(`/api/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error(`Failed to read job: ${response.status}`);
  }
  return response.json();
}

function renderJob(job) {
  statusEl.textContent = `state: ${job.state}`;
  if (job.state === 'succeeded') {
    resultEl.textContent = JSON.stringify(job.result, null, 2);
  } else if (job.state === 'failed') {
    resultEl.textContent = job.error || 'Unknown error';
  }
}

function beginPolling(jobId) {
  stopPolling();
  pollTimer = setInterval(async () => {
    try {
      const job = await fetchJob(jobId);
      renderJob(job);
      if (job.state === 'succeeded' || job.state === 'failed') {
        stopPolling();
      }
    } catch (error) {
      stopPolling();
      resultEl.textContent = String(error);
    }
  }, 1000);
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  stopPolling();
  statusEl.textContent = 'state: queued';
  resultEl.textContent = '';

  const payload = {
    url: document.getElementById('url').value,
    extraction_type: document.getElementById('extraction_type').value,
  };

  const response = await fetch('/api/jobs', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    resultEl.textContent = `Failed to create job: ${response.status}`;
    return;
  }

  const {job_id: jobId} = await response.json();
  jobIdEl.textContent = `job_id: ${jobId}`;
  beginPolling(jobId);
});
