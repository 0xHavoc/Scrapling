const form = document.getElementById('scrape-form');
const runBtn = document.getElementById('run-btn');
const statusEl = document.getElementById('status');
const validationErrorEl = document.getElementById('validation-error');

const outputExtracted = document.getElementById('output-extracted');
const outputRaw = document.getElementById('output-raw');
const outputLogs = document.getElementById('output-logs');

const copyBtn = document.getElementById('copy-btn');
const downloadBtn = document.getElementById('download-btn');

let activeTab = 'extracted';
let state = {
  extracted: 'No results yet.',
  raw: 'No raw content yet.',
  logs: 'No logs yet.',
};

function setStatus(text) {
  statusEl.textContent = text;
}

function setLoading(loading) {
  runBtn.disabled = loading;
  runBtn.textContent = loading ? 'Running…' : 'Run';
}

function showValidationError(message) {
  validationErrorEl.textContent = message;
  validationErrorEl.classList.remove('hidden');
}

function clearValidationError() {
  validationErrorEl.classList.add('hidden');
  validationErrorEl.textContent = '';
}

function parseOptionalJson(raw, fieldName) {
  if (!raw.trim()) return {};
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed !== 'object' || Array.isArray(parsed) || parsed === null) {
      throw new Error('must be a JSON object');
    }
    return parsed;
  } catch (error) {
    throw new Error(`${fieldName} must be valid JSON object (${error.message})`);
  }
}

function validateInputs(formData) {
  const url = formData.get('url')?.trim();
  if (!url) {
    throw new Error('URL is required.');
  }

  let parsedUrl;
  try {
    parsedUrl = new URL(url);
  } catch {
    throw new Error('URL is invalid.');
  }

  if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
    throw new Error('URL must start with http:// or https://');
  }

  const timeoutValue = formData.get('timeout');
  const timeout = Number(timeoutValue);
  if (!Number.isInteger(timeout) || timeout <= 0) {
    throw new Error('Timeout must be a positive integer in milliseconds.');
  }

  const headers = parseOptionalJson(formData.get('headers') || '', 'Headers');
  const cookies = parseOptionalJson(formData.get('cookies') || '', 'Cookies');
  const params = parseOptionalJson(formData.get('params') || '', 'Params');

  return {
    url,
    fetcher: formData.get('fetcher') || 'requests',
    timeout,
    selector: formData.get('selector')?.trim() || '',
    headers,
    cookies,
    params,
  };
}

function setOutputs(nextState) {
  state = { ...state, ...nextState };
  outputExtracted.textContent = state.extracted;
  outputRaw.textContent = state.raw;
  outputLogs.textContent = state.logs;
}

async function runWorkflow(payload) {
  const requestLogs = [];

  requestLogs.push({ step: 'fetch:start', endpoint: '/api/fetch', payload });
  const fetchRes = await fetch('/api/fetch', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url: payload.url,
      fetcher: payload.fetcher,
      timeout: payload.timeout,
      headers: payload.headers,
      cookies: payload.cookies,
      params: payload.params,
    }),
  });

  let fetchJson;
  try {
    fetchJson = await fetchRes.json();
  } catch {
    fetchJson = {};
  }

  requestLogs.push({
    step: 'fetch:done',
    status: fetchRes.status,
    ok: fetchRes.ok,
    body: fetchJson,
  });

  if (!fetchRes.ok) {
    throw new Error(fetchJson?.error || `Fetch failed with status ${fetchRes.status}`);
  }

  const rawContent = fetchJson?.html ?? fetchJson?.text ?? '';
  setOutputs({ raw: rawContent || 'No raw content returned.' });

  requestLogs.push({
    step: 'extract:start',
    endpoint: '/api/extract',
    payload: {
      selector: payload.selector,
      hasRawContent: Boolean(rawContent),
    },
  });

  const extractRes = await fetch('/api/extract', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      selector: payload.selector,
      html: rawContent,
      url: payload.url,
    }),
  });

  let extractJson;
  try {
    extractJson = await extractRes.json();
  } catch {
    extractJson = {};
  }

  requestLogs.push({
    step: 'extract:done',
    status: extractRes.status,
    ok: extractRes.ok,
    body: extractJson,
  });

  if (!extractRes.ok) {
    throw new Error(extractJson?.error || `Extract failed with status ${extractRes.status}`);
  }

  setOutputs({
    extracted: JSON.stringify(extractJson, null, 2),
    logs: JSON.stringify(requestLogs, null, 2),
  });
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  clearValidationError();

  try {
    const payload = validateInputs(new FormData(form));

    setLoading(true);
    setStatus('Fetching page…');
    setOutputs({
      extracted: 'Running extraction…',
      raw: 'Fetching raw content…',
      logs: 'Preparing request logs…',
    });

    await runWorkflow(payload);
    setStatus('Done');
  } catch (error) {
    setStatus('Failed');
    const friendlyMessage = error instanceof Error ? error.message : 'Unexpected error occurred.';
    showValidationError(friendlyMessage);
    setOutputs({ logs: `${state.logs}\n\nError: ${friendlyMessage}` });
  } finally {
    setLoading(false);
  }
});

document.querySelectorAll('.tab').forEach((tabButton) => {
  tabButton.addEventListener('click', () => {
    const nextTab = tabButton.dataset.tab;
    if (!nextTab) return;

    activeTab = nextTab;
    document.querySelectorAll('.tab').forEach((tab) => tab.classList.remove('active'));
    document.querySelectorAll('.panel').forEach((panel) => panel.classList.remove('active'));

    tabButton.classList.add('active');
    document.getElementById(`panel-${nextTab}`)?.classList.add('active');
  });
});

function getActiveTabContent() {
  return state[activeTab] || '';
}

copyBtn.addEventListener('click', async () => {
  const text = getActiveTabContent();
  if (!text) return;

  try {
    await navigator.clipboard.writeText(text);
    setStatus('Copied active tab content');
  } catch {
    showValidationError('Unable to copy content to clipboard.');
  }
});

downloadBtn.addEventListener('click', () => {
  const content = getActiveTabContent();
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `scrapling-${activeTab}-${Date.now()}.txt`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
  setStatus('Downloaded active tab content');
});
