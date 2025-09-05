// Light state and helpers
const state = {
  targetInputId: null,
  stream: null,
  capturedImageBlob: null,
  worker: null,
  lastFocused: null,
  provider: 'tesseract',
  geminiKey: '',
};

// DOM references
const q = (sel) => document.querySelector(sel);
const qa = (sel) => Array.from(document.querySelectorAll(sel));

function renderKatex(elementId, expr) {
  const el = q(`#${elementId}`);
  if (!el) return;
  try {
    window.katex.render(expr || '', el, { throwOnError: false });
  } catch (e) {
    el.textContent = expr || '';
  }
}

// KaTeX formatting helper: convert simple mathjs-like to TeX-ish quickly
function toTexQuick(expr) {
  if (!expr) return '';
  return expr
    .replaceAll('*', ' \\cdot ')
    .replaceAll('^', '^{')
    .replace(/\^{\((.*?)\)}/g, '^{$1}')
    .replaceAll('exp(', 'e^{')
    .replaceAll(')', '}')
    .replaceAll('integrate', '\\int')
    .replaceAll('sumN', '\\sum');
}

// Math.js setup with custom helpers
const math = window.math;

// numeric integration via adaptive Simpson's rule (simple implementation)
function integrateNumeric(fn, a, b, maxDepth = 12, eps = 1e-7) {
  const f = (x) => {
    try {
      const y = fn(x);
      if (typeof y === 'number') return y;
      if (y && typeof y.valueOf === 'function') return Number(y.valueOf());
      return Number(y);
    } catch {
      return NaN;
    }
  };
  function simpson(f, a, b) {
    const c = (a + b) / 2;
    return (b - a) / 6 * (f(a) + 4 * f(c) + f(b));
  }
  function recurse(f, a, b, eps, S, depth) {
    const c = (a + b) / 2;
    const Sleft = simpson(f, a, c);
    const Sright = simpson(f, c, b);
    const S2 = Sleft + Sright;
    if (depth <= 0 || Math.abs(S2 - S) <= 15 * eps) return S2 + (S2 - S) / 15;
    return recurse(f, a, c, eps / 2, Sleft, depth - 1) + recurse(f, c, b, eps / 2, Sright, depth - 1);
  }
  const S = simpson(f, a, b);
  return recurse(f, a, b, eps, S, maxDepth);
}

// finite sum
function sumN(fn, n0, n1) {
  let acc = 0;
  for (let n = Math.trunc(n0); n <= Math.trunc(n1); n++) {
    acc += Number(fn(n));
  }
  return acc;
}

// Build mathjs scope from variable table
function buildScope() {
  const scope = {
    exp: Math.exp,
    integrate: (fn, a, b) => integrateNumeric(fn, Number(a), Number(b)),
    sumN: (fn, a, b) => sumN(fn, Number(a), Number(b)),
  };
  // variables table
  qa('#varsBody tr').forEach((row) => {
    const name = row.querySelector('.var-name')?.value?.trim();
    const valueText = row.querySelector('.var-value')?.value?.trim();
    if (!name) return;
    if (valueText === undefined || valueText === '') return;
    const parsed = Number(valueText);
    scope[name] = Number.isFinite(parsed) ? parsed : valueText;
  });
  return scope;
}

// Parse expression into a callable function of t
function buildFunctionOfT(expr, scopeBase) {
  if (!expr) return (t) => NaN;
  const scope = { ...scopeBase };
  try {
    // Sanitize OCR quirks and build a mathjs lambda t -> (expr)
    const cleaned = sanitizeExpression(expr);
    const wrapped = `t -> (${cleaned})`;
    const node = math.parse(wrapped);
    const code = node.compile();
    const fn = code.evaluate(scope);
    return (t) => {
      try {
        const y = fn(t);
        if (typeof y === 'number') return y;
        if (y && typeof y.valueOf === 'function') return Number(y.valueOf());
        return Number(y);
      } catch {
        return NaN;
      }
    };
  } catch (e) {
    console.error('Function parse error', e);
    return (t) => NaN;
  }
}

// Evaluate main equation numeric value
function evaluateAll() {
  const i1Expr = q('#i1').value.trim();
  const i2Expr = q('#i2').value.trim();
  const i3Expr = q('#i3').value.trim();
  const mainExpr = q('#mainEq').value.trim();

  const scope = buildScope();
  const I1 = buildFunctionOfT(i1Expr, scope);
  const I2 = buildFunctionOfT(i2Expr, scope);
  const I3 = buildFunctionOfT(i3Expr, scope);

  // Expose to scope so main equation can call them
  scope.I1 = I1;
  scope.I2 = I2;
  scope.I3 = I3;

  let value;
  try {
    const node = math.parse(sanitizeExpression(mainExpr));
    const code = node.compile();
    value = code.evaluate(scope);
  } catch (e) {
    q('#result').innerHTML = `<span style="color:#ef4444">Parse error: ${e.message}</span>`;
    return;
  }

  const out = Number(value);
  if (!Number.isFinite(out)) {
    q('#result').innerHTML = `<span style="color:#ef4444">Result is not a finite number.</span>`;
  } else {
    q('#result').textContent = `Result: ${out}`;
  }
}

// UI wiring
function updatePreviews() {
  renderKatex('i1Preview', toTexQuick(q('#i1').value));
  renderKatex('i2Preview', toTexQuick(q('#i2').value));
  renderKatex('i3Preview', toTexQuick(q('#i3').value));
  renderKatex('mainPreview', toTexQuick(q('#mainEq').value));
}

qa('textarea').forEach((el) => el.addEventListener('input', updatePreviews));
// track focus for palette insertion
document.addEventListener('focusin', (e) => {
  if (e.target.matches('textarea, input')) state.lastFocused = e.target;
});
updatePreviews();

// Vars table controls
q('#addVar').addEventListener('click', () => {
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td><input class="var-name" placeholder="name" /></td>
    <td><input class="var-value" placeholder="value" /></td>
    <td><button class="scan-btn" data-target="prev">📷</button></td>
    <td><button class="row-del">✖</button></td>
  `;
  q('#varsBody').appendChild(tr);
});

document.addEventListener('click', (e) => {
  if (e.target.matches('.row-del')) {
    e.target.closest('tr')?.remove();
  }
});

q('#evaluate').addEventListener('click', evaluateAll);
q('#clearAll').addEventListener('click', () => {
  qa('textarea').forEach((t) => (t.value = ''));
  qa('#varsBody .var-value').forEach((i) => (i.value = ''));
  updatePreviews();
  q('#result').textContent = '';
});
q('#copyResult').addEventListener('click', async () => {
  const text = q('#result').textContent || '';
  try { await navigator.clipboard.writeText(text); } catch {}
});

// Persist inputs
function saveState() {
  const vars = qa('#varsBody tr').map((row) => ({
    name: row.querySelector('.var-name')?.value || '',
    value: row.querySelector('.var-value')?.value || '',
  }));
  const payload = {
    vars,
    i1: q('#i1').value,
    i2: q('#i2').value,
    i3: q('#i3').value,
    main: q('#mainEq').value,
  };
  localStorage.setItem('eqscan_state', JSON.stringify(payload));
}
function loadState() {
  const raw = localStorage.getItem('eqscan_state');
  if (!raw) return;
  try {
    const data = JSON.parse(raw);
    if (Array.isArray(data.vars)) {
      q('#varsBody').innerHTML = '';
      data.vars.forEach((v) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><input class="var-name" placeholder="name" value="${v.name || ''}" /></td>
          <td><input class="var-value" placeholder="value" value="${v.value || ''}" /></td>
          <td><button class="scan-btn" data-target="prev">📷</button></td>
          <td><button class="row-del">✖</button></td>
        `;
        q('#varsBody').appendChild(tr);
      });
    }
    if (typeof data.i1 === 'string') q('#i1').value = data.i1;
    if (typeof data.i2 === 'string') q('#i2').value = data.i2;
    if (typeof data.i3 === 'string') q('#i3').value = data.i3;
    if (typeof data.main === 'string') q('#mainEq').value = data.main;
  } catch {}
}
setInterval(saveState, 1000);

// Camera and OCR
async function ensureWorker() {
  if (state.worker) return state.worker;
  state.worker = await Tesseract.createWorker({
    langPath: 'https://tessdata.projectnaptha.com/4.0.0',
    logger: () => {},
  });
  await state.worker.loadLanguage('eng+equ');
  await state.worker.initialize('eng+equ');
  await state.worker.setParameters({
    preserve_interword_spaces: '1',
    tessedit_pageseg_mode: Tesseract.PSM.SPARSE_TEXT,
    user_defined_dpi: '300',
  });
  return state.worker;
}

async function openCamera(targetId) {
  state.targetInputId = targetId;
  q('#cameraModal').classList.remove('hidden');
  try {
    state.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
    q('#video').srcObject = state.stream;
  } catch (e) {
    q('#ocrStatus').textContent = 'Camera error: ' + e.message;
  }
}

function closeCamera() {
  q('#cameraModal').classList.add('hidden');
  if (state.stream) {
    state.stream.getTracks().forEach((t) => t.stop());
    state.stream = null;
  }
  state.capturedImageBlob = null;
  q('#canvas').classList.add('hidden');
  q('#ocrStatus').textContent = '';
}

qa('.scan-btn').forEach((btn) => {
  btn.addEventListener('click', () => openCamera(btn.dataset.target));
});

q('#closeModal').addEventListener('click', closeCamera);

q('#capture').addEventListener('click', () => {
  const video = q('#video');
  const canvas = q('#canvas');
  const ctx = canvas.getContext('2d');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.drawImage(video, 0, 0);
  applyPreprocess(canvas);
  canvas.classList.remove('hidden');
  canvas.toBlob((blob) => (state.capturedImageBlob = blob));
});

q('#recognize').addEventListener('click', async () => {
  if (!state.capturedImageBlob) {
    q('#ocrStatus').textContent = 'Capture an image first.';
    return;
  }
  q('#ocrStatus').textContent = 'Recognizing...';
  try {
    const text = await recognizeWithTimeout(state.provider);
    injectOcrText(text);
    q('#ocrStatus').textContent = 'Done';
    updatePreviews();
  } catch (e) {
    q('#ocrStatus').textContent = 'OCR error: ' + e.message;
  }
});

// Gallery upload -> OCR
q('#fileInput').addEventListener('change', async (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  state.capturedImageBlob = file;
  q('#ocrStatus').textContent = 'Image loaded from gallery.';
  const img = new Image();
  img.onload = () => {
    const canvas = q('#canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = img.width;
    canvas.height = img.height;
    ctx.drawImage(img, 0, 0);
    applyPreprocess(canvas);
    canvas.classList.remove('hidden');
  };
  img.src = URL.createObjectURL(file);
});

function injectOcrText(text) {
  if (!state.targetInputId) return;
  if (state.targetInputId === 'prev') {
    // insert into selected variable value cell if any focused
    const active = document.activeElement;
    if (active && active.classList.contains('var-value')) {
      active.value = text;
    }
  } else {
    const el = q(`#${state.targetInputId}`);
    if (el) el.value = (el.value ? el.value + ' ' : '') + text;
  }
}

// Initialize with a simple example so users see the format
window.addEventListener('DOMContentLoaded', () => {
  loadState();
  // Load provider settings
  state.provider = localStorage.getItem('eqscan_provider') || 'tesseract';
  state.geminiKey = localStorage.getItem('eqscan_gemini_key') || '';
  const provSel = q('#ocrProvider');
  const keyInput = q('#geminiKey');
  if (provSel) provSel.value = state.provider;
  if (keyInput) keyInput.value = state.geminiKey;
  if (!q('#i1').value) q('#i1').value = 'D0 * exp(-alpha1 * t^beta1) + Q * exp(-alpha1 * t^beta1)';
  if (!q('#i2').value) q('#i2').value = 'D0 * exp(-alpha1 * t^beta1) + Q * (exp(-alpha1 * t^beta1) - alpha)';
  if (!q('#i3').value) q('#i3').value = '(b*mu - D0) * exp(-alpha1 * t^beta1) - b * exp(-alpha1 * t^(beta1+2)) + Q * exp(-alpha1 * t^beta1) * (1 - alpha * exp(-alpha1 * mu^beta1))';
  if (!q('#mainEq').value) q('#mainEq').value = 'integrate(t -> I1(t) * exp(-R*t), theta, t1) + integrate(t -> I2(t) * exp(-R*t), t1, mu) + integrate(t -> I3(t) * exp(-R*t), mu, T)';
  updatePreviews();
});

// Symbol palette insertion
q('#symbolPalette')?.addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-insert]');
  if (!btn) return;
  const insert = btn.getAttribute('data-insert');
  const target = state.lastFocused || q('#mainEq');
  if (!target) return;
  const start = target.selectionStart ?? target.value.length;
  const end = target.selectionEnd ?? target.value.length;
  const before = target.value.slice(0, start);
  const after = target.value.slice(end);
  target.value = `${before}${insert}${after}`;
  const cursor = start + insert.length;
  target.focus();
  target.setSelectionRange(cursor, cursor);
  updatePreviews();
});

// Provider UI
q('#ocrProvider').addEventListener('change', (e) => {
  state.provider = e.target.value;
  localStorage.setItem('eqscan_provider', state.provider);
});
q('#geminiKey').addEventListener('input', (e) => {
  state.geminiKey = e.target.value.trim();
  localStorage.setItem('eqscan_gemini_key', state.geminiKey);
});

// Simple preprocessing: grayscale + contrast + threshold
function applyPreprocess(canvas) {
  const ctx = canvas.getContext('2d');
  const img = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = img.data;
  // grayscale + contrast
  const contrast = 1.2; // >1 increases contrast
  const threshold = 180; // 0-255
  for (let i = 0; i < data.length; i += 4) {
    const r = data[i], g = data[i + 1], b = data[i + 2];
    let y = 0.2126 * r + 0.7152 * g + 0.0722 * b; // luma
    y = (y - 128) * contrast + 128;
    const v = y > threshold ? 255 : 0;
    data[i] = data[i + 1] = data[i + 2] = v;
  }
  ctx.putImageData(img, 0, 0);
}

// Normalize OCR output into ASCII-friendly math text
function normalizeOcrText(text) {
  if (!text) return '';
  let t = text
    .replace(/[\t\r]+/g, ' ')
    .replace(/\u00A0/g, ' ')
    .replace(/[\u2013\u2014]/g, '-')
    .replace(/[\u2212]/g, '-')
    .replace(/[\u00B7\u22C5\u2022]/g, '*')
    .replace(/[\u2264]/g, '<=')
    .replace(/[\u2265]/g, '>=')
    .replace(/[\u2260]/g, '!=')
    .replace(/[\u2248]/g, 'approx')
    .replace(/[\u2211]/g, 'sumN')
    .replace(/[\u221E]/g, 'Infinity');

  const greekMap = {
    'π': 'pi', 'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'θ': 'theta', 'μ': 'mu', 'λ': 'lambda', 'σ': 'sigma', 'Δ': 'Delta'
  };
  t = t.replace(/[παβγθμλσΔ]/g, (m) => greekMap[m] || m);

  const superMap = { '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', '⁰': '0', '⁻': '-' };
  t = t.replace(/[¹²³⁴⁵⁶⁷⁸⁹⁰⁻]/g, (m) => '^' + (superMap[m] || ''));

  t = t.replace(/\s+/g, ' ').trim();
  return t;
}

// Additional expression sanitization for mathjs parsing
function sanitizeExpression(expr) {
  if (!expr) return '';
  let t = expr;
  // replace fancy minus and dot and division slashes
  t = t.replace(/[\u2212\u2013\u2014]/g, '-').replace(/[\u00B7\u22C5\u2022]/g, '*').replace(/[\u2044]/g, '/');
  // convert unicode superscripts handled earlier, ensure ^(...) is wrapped
  t = t.replace(/\^\s*([A-Za-z0-9]+)/g, '^($1)');
  // convert I1[t] style to I1(t)
  t = t.replace(/([A-Za-z_]\w*)\s*\[\s*([A-Za-z_]\w*)\s*\]/g, '$1($2)');
  // replace exp-notation e^-x with exp(-x)
  t = t.replace(/e\s*\^\s*\(/g, 'exp(');
  // ensure arrow spacing: t-> to t ->
  t = t.replace(/(\b\w+)\s*->/g, '$1 ->');
  // remove stray backslashes
  t = t.replace(/\\+/g, '');
  // collapse whitespace
  t = t.replace(/\s+/g, ' ').trim();
  return t;
}

// Recognizer with timeout and provider support
async function recognizeWithTimeout(provider) {
  const timeoutMs = 30000; // 30s hard timeout
  const timeout = new Promise((_, reject) => setTimeout(() => reject(new Error('Recognition timeout')), timeoutMs));
  if (provider === 'gemini') {
    const work = recognizeGemini();
    const text = await Promise.race([work, timeout]);
    return normalizeOcrText(text);
  } else {
    const work = (async () => {
      const worker = await ensureWorker();
      const { data } = await worker.recognize(state.capturedImageBlob);
      return data.text || '';
    })();
    const text = await Promise.race([work, timeout]);
    return normalizeOcrText(text);
  }
}

async function recognizeGemini() {
  if (!state.geminiKey) throw new Error('Missing Gemini API key');
  const api = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent';
  const imageData = await blobToBase64(state.capturedImageBlob);
  const prompt = 'Extract the mathematical expression from this image as plain text suitable for mathjs. Use ASCII operators, caret ^ for powers, exp() for exponentials, and write integrals as integrate(t -> <expr>, a, b) and sums as sumN(n -> <expr>, n0, n1). Output only the expression, no commentary.';
  const body = {
    contents: [{
      parts: [
        { text: prompt },
        { inline_data: { mime_type: state.capturedImageBlob.type || 'image/png', data: imageData } }
      ]
    }]
  };
  const url = `${api}?key=${encodeURIComponent(state.geminiKey)}`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(`Gemini error ${res.status}`);
  const json = await res.json();
  const text = json?.candidates?.[0]?.content?.parts?.map((p) => p.text).join(' ') || '';
  return text.trim();
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(reader.error);
    reader.onload = () => {
      const result = reader.result.split(',')[1];
      resolve(result);
    };
    reader.readAsDataURL(blob);
  });
}

