const editor = document.querySelector('#python-editor');
const runButton = document.querySelector('#run-button');
const clearButton = document.querySelector('#clear-button');
const output = document.querySelector('#console-output');
const status = document.querySelector('#runtime-status');
const sampleTemplate = document.querySelector('#sample-code');

let pyodide = null;
let isRunning = false;

const appendMessage = (message, type = 'info') => {
  const time = new Date().toLocaleTimeString();
  const line = document.createElement('div');
  line.className = `console-line ${type}`;

  const timeSpan = document.createElement('span');
  timeSpan.className = 'timestamp';
  timeSpan.textContent = time;

  const messageSpan = document.createElement('span');
  messageSpan.className = 'message';
  messageSpan.textContent = message;

  line.append(timeSpan, messageSpan);
  output.append(line);
  output.scrollTop = output.scrollHeight;
};

const setRunningState = (running) => {
  isRunning = running;
  runButton.disabled = running || !pyodide;
  runButton.textContent = running ? 'Running…' : 'Run ▶';
};

const initEditor = () => {
  if (!editor.value.trim() && sampleTemplate) {
    editor.value = sampleTemplate.innerHTML.trim();
  }
};

const captureConsole = () => {
  if (!pyodide) return;
  const normalize = (text) => text.replace(/\s+$/, '');
  pyodide.setStdout({
    batched: (text) => {
      const cleaned = normalize(text);
      if (cleaned.length) {
        appendMessage(cleaned);
      }
    },
  });
  pyodide.setStderr({
    batched: (text) => {
      const cleaned = normalize(text);
      if (cleaned.length) {
        appendMessage(cleaned, 'error');
      }
    },
  });
};

const loadPyodideRuntime = async () => {
  try {
    status.textContent = 'Fetching Pyodide…';
    pyodide = await loadPyodide({ indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/' });
    captureConsole();
    status.textContent = 'Python ready';
    runButton.disabled = false;
    appendMessage('✅ Pyodide loaded. You can run Python code now.');
  } catch (error) {
    status.textContent = 'Failed to load Pyodide';
    appendMessage(`❌ Failed to load Python runtime: ${error.message}`, 'error');
    console.error(error);
  }
};

const runPython = async (code) => {
  if (!pyodide) {
    appendMessage('⚠️ Pyodide is not ready yet. Please wait a moment.', 'warning');
    return;
  }

  if (!code.trim()) {
    appendMessage('⚠️ Nothing to run. Please enter some Python code.', 'warning');
    return;
  }

  setRunningState(true);
  appendMessage('▶ Running code…');

  try {
    const result = await pyodide.runPythonAsync(code);
    if (typeof result !== 'undefined') {
      appendMessage(String(result));
    }
  } catch (error) {
    appendMessage(`Traceback (most recent call last):\n${error}`, 'error');
  } finally {
    setRunningState(false);
  }
};

runButton.addEventListener('click', () => runPython(editor.value));
clearButton.addEventListener('click', () => {
  output.textContent = '';
  appendMessage('🧹 Console cleared.');
});

editor.addEventListener('keydown', (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
    event.preventDefault();
    runPython(editor.value);
  }
});

initEditor();
loadPyodideRuntime();

// Optional: respect system theme and allow toggling light/dark via keyboard shortcut
const prefersLight = window.matchMedia('(prefers-color-scheme: light)');
const toggleLightMode = (enable) => {
  document.body.classList.toggle('light-mode', enable);
};

toggleLightMode(prefersLight.matches);
prefersLight.addEventListener('change', (event) => toggleLightMode(event.matches));

document.addEventListener('keydown', (event) => {
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key.toLowerCase() === 'l') {
    toggleLightMode(!document.body.classList.contains('light-mode'));
  }
});
