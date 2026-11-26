import './styles/workbench.css';
import Lenis from 'lenis';
import { animate, inView, stagger } from 'motion';
import { Sun, Moon, createElement } from 'lucide';
import {
  DEPLOYMENT_MODES,
  MOCK_ENDPOINTS,
  OPENAPI_SAMPLES,
  type MockEndpoint,
  type OpenApiSample,
} from './data/mockScenarios';

// Smooth scrolling
const lenis = new Lenis({
  duration: 1.0,
  easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
  smoothWheel: true,
});

const raf = (time: number): void => {
  lenis.raf(time);
  requestAnimationFrame(raf);
};
requestAnimationFrame(raf);

document.querySelectorAll<HTMLAnchorElement>('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener('click', (e) => {
    const id = anchor.getAttribute('href')?.slice(1) ?? '';
    const target = id ? document.getElementById(id) : null;
    if (target) {
      e.preventDefault();
      lenis.scrollTo(target, { offset: -70 });
    }
  });
});

// Theme toggle with Lucide icons
const themeBtn = document.getElementById('wb-theme-btn');
const renderThemeIcon = (): void => {
  if (!themeBtn) return;
  const theme = document.documentElement.getAttribute('data-theme') ?? 'dark';
  themeBtn.innerHTML = '';
  const icon = createElement(theme === 'dark' ? Sun : Moon, { width: 15, height: 15 });
  themeBtn.appendChild(icon);
};

renderThemeIcon();
themeBtn?.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme') ?? 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  renderThemeIcon();
});

// Interactive API Simulator Workbench
const routeTabsEl = document.getElementById('wb-route-tabs');
const statusSelect = document.getElementById('wb-status-select') as HTMLSelectElement | null;
const latencyRange = document.getElementById('wb-latency-range') as HTMLInputElement | null;
const latencyValEl = document.getElementById('wb-latency-val');
const chaosCheck = document.getElementById('wb-chaos-check') as HTMLInputElement | null;
const sendBtn = document.getElementById('wb-send-btn') as HTMLButtonElement | null;
const jsonOutputEl = document.getElementById('wb-json-output');
const elapsedLabelEl = document.getElementById('wb-elapsed-label');
const simStatusPill = document.getElementById('wb-sim-status-pill');
const requestLogEl = document.getElementById('wb-request-log');
const clearLogBtn = document.getElementById('wb-clear-log');

let activeEndpoint: MockEndpoint = MOCK_ENDPOINTS[0]!;

const renderRouteTabs = (): void => {
  if (!routeTabsEl) return;
  routeTabsEl.innerHTML = '';
  MOCK_ENDPOINTS.forEach((ep) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'wb-route-btn wb-mono';
    btn.setAttribute('data-active', String(ep.id === activeEndpoint.id));
    btn.innerHTML = `<span class="wb-method">${ep.method}</span><span>${ep.path}</span>`;
    btn.addEventListener('click', () => {
      activeEndpoint = ep;
      if (statusSelect) statusSelect.value = String(ep.defaultStatus);
      renderRouteTabs();
      renderPayloadPreview(ep.defaultStatus, Number(latencyRange?.value ?? 180));
    });
    routeTabsEl.appendChild(btn);
  });
};

const renderPayloadPreview = (status: number, elapsedMs: number, chaosTriggered = false): void => {
  const payload = chaosTriggered
    ? { ok: false, error: 'chaos_injected_unavailable', status: 503 }
    : (activeEndpoint.payloads[status] ?? activeEndpoint.payloads[200] ?? {});
  if (jsonOutputEl) {
    jsonOutputEl.textContent = JSON.stringify(payload, null, 2);
  }
  if (elapsedLabelEl) {
    elapsedLabelEl.textContent = `${elapsedMs}ms · ${chaosTriggered ? '503 Chaos' : `${status} JSON`}`;
  }
};

const appendRequestLog = (method: string, path: string, status: number, elapsedMs: number): void => {
  if (!requestLogEl) return;
  const row = document.createElement('div');
  row.className = 'wb-log-item';
  const color = status >= 500 ? 'var(--wb-danger)' : status >= 400 ? 'var(--wb-amber)' : 'var(--wb-emerald)';
  row.innerHTML = `<span><strong style="color: var(--wb-amber);">${method}</strong> ${path}</span><span style="color: ${color}; font-weight: 700;">${status} · ${elapsedMs}ms</span>`;
  requestLogEl.prepend(row);
};

latencyRange?.addEventListener('input', () => {
  if (latencyValEl) latencyValEl.textContent = `${latencyRange.value}ms`;
});

sendBtn?.addEventListener('click', async () => {
  if (!sendBtn) return;
  const delay = Number(latencyRange?.value ?? 180);
  const selectedStatus = Number(statusSelect?.value ?? activeEndpoint.defaultStatus);
  const chaos = Boolean(chaosCheck?.checked) && Math.random() < 0.35;

  sendBtn.disabled = true;
  if (simStatusPill) {
    simStatusPill.textContent = 'IN FLIGHT...';
    simStatusPill.style.color = 'var(--wb-amber)';
  }

  const started = performance.now();
  await new Promise((resolve) => setTimeout(resolve, delay));
  const actualMs = Math.max(1, Math.round(performance.now() - started));
  const finalStatus = chaos ? 503 : selectedStatus;

  renderPayloadPreview(selectedStatus, actualMs, chaos);
  appendRequestLog(activeEndpoint.method, activeEndpoint.path, finalStatus, actualMs);

  if (simStatusPill) {
    simStatusPill.textContent = `${finalStatus} OK`;
    simStatusPill.style.color = finalStatus >= 400 ? 'var(--wb-danger)' : 'var(--wb-emerald)';
  }
  sendBtn.disabled = false;
});

clearLogBtn?.addEventListener('click', () => {
  if (requestLogEl) requestLogEl.innerHTML = '';
});

renderRouteTabs();
renderPayloadPreview(activeEndpoint.defaultStatus, 180);
appendRequestLog(activeEndpoint.method, activeEndpoint.path, activeEndpoint.defaultStatus, 180);

// OpenAPI -> Mock Routes Converter
const specTabsEl = document.getElementById('wb-spec-tabs');
const specPreviewEl = document.getElementById('wb-spec-preview');
const genRoutesEl = document.getElementById('wb-generated-routes');
const parseBtn = document.getElementById('wb-parse-btn');
const genBadge = document.getElementById('wb-gen-badge');

let activeSpec: OpenApiSample = OPENAPI_SAMPLES[0]!;

const renderOpenApiSection = (): void => {
  if (specTabsEl) {
    specTabsEl.innerHTML = '';
    OPENAPI_SAMPLES.forEach((sample) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'wb-seg-btn';
      btn.textContent = sample.label;
      btn.setAttribute('data-active', String(sample.id === activeSpec.id));
      btn.addEventListener('click', () => {
        activeSpec = sample;
        renderOpenApiSection();
      });
      specTabsEl.appendChild(btn);
    });
  }

  if (specPreviewEl) specPreviewEl.textContent = activeSpec.spec;
  if (genRoutesEl) {
    genRoutesEl.innerHTML = '';
    activeSpec.generatedRoutes.forEach((route) => {
      const row = document.createElement('div');
      row.className = 'wb-gen-row';
      row.innerHTML = `
        <div class="wb-mono" style="font-size: 0.8rem;">
          <strong style="color: var(--wb-amber); margin-right: 0.5rem;">${route.method}</strong>
          <span>${route.path}</span>
        </div>
        <span class="wb-mono" style="font-size: 0.72rem; color: var(--wb-emerald);">${route.status} · ${route.note}</span>
      `;
      genRoutesEl.appendChild(row);
    });
  }
};

parseBtn?.addEventListener('click', () => {
  if (genBadge) genBadge.textContent = 'REGENERATED ✓';
  if (genRoutesEl) {
    animate(genRoutesEl.children, { opacity: [0.3, 1], x: [-8, 0] }, { duration: 0.3, delay: stagger(0.06) });
  }
});

renderOpenApiSection();

// On-Premise vs SaaS Switcher
const deployTabsEl = document.getElementById('wb-deploy-tabs');
const deployTitleEl = document.getElementById('wb-deploy-title');
const deploySubEl = document.getElementById('wb-deploy-sub');
const deployCmdEl = document.getElementById('wb-deploy-cmd');
const deployHighlightsEl = document.getElementById('wb-deploy-highlights');
const deployArchEl = document.getElementById('wb-deploy-arch');
const copyCmdBtn = document.getElementById('wb-copy-cmd');

let activeModeId: 'onprem' | 'saas' = 'onprem';

const renderDeploymentMode = (): void => {
  const mode = DEPLOYMENT_MODES.find((m) => m.id === activeModeId) ?? DEPLOYMENT_MODES[0]!;
  if (deployTitleEl) deployTitleEl.textContent = mode.title;
  if (deploySubEl) deploySubEl.textContent = mode.subtitle;
  if (deployCmdEl) deployCmdEl.textContent = `$ ${mode.command}`;

  if (deployHighlightsEl) {
    deployHighlightsEl.innerHTML = mode.highlights.map((h) => `<li>${h}</li>`).join('');
  }
  if (deployArchEl) {
    deployArchEl.innerHTML = mode.architecture
      .map(
        (item) => `
      <div class="wb-arch-cell">
        <div class="wb-mono" style="font-size: 0.7rem; color: var(--wb-muted);">${item.label}</div>
        <div style="font-weight: 700; font-size: 0.88rem; margin-top: 0.25rem;">${item.value}</div>
      </div>`,
      )
      .join('');
  }
};

deployTabsEl?.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach((btn) => {
  btn.addEventListener('click', () => {
    const modeVal = btn.dataset.mode === 'saas' ? 'saas' : 'onprem';
    activeModeId = modeVal;
    deployTabsEl.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach((b) => {
      b.setAttribute('data-active', String(b === btn));
    });
    renderDeploymentMode();
  });
});

copyCmdBtn?.addEventListener('click', async () => {
  const mode = DEPLOYMENT_MODES.find((m) => m.id === activeModeId) ?? DEPLOYMENT_MODES[0]!;
  await navigator.clipboard.writeText(mode.command);
  copyCmdBtn.textContent = 'Copied ✓';
  setTimeout(() => {
    copyCmdBtn.textContent = 'Copy';
  }, 1400);
});

renderDeploymentMode();

// Entrance & scroll animations
animate('.wb-animate', { opacity: [0, 1], y: [14, 0] }, { duration: 0.45, delay: stagger(0.06), ease: 'easeOut' });
document.querySelectorAll<HTMLElement>('.wb-reveal').forEach((el) => {
  el.style.opacity = '0';
  inView(el, () => {
    animate(el, { opacity: [0, 1], y: [18, 0] }, { duration: 0.45, ease: 'easeOut' });
  });
});
