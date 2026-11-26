export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';

export interface MockEndpoint {
  readonly id: string;
  readonly method: HttpMethod;
  readonly path: string;
  readonly summary: string;
  readonly defaultStatus: number;
  readonly payloads: Record<number, Record<string, unknown>>;
}

export interface OpenApiSample {
  readonly id: string;
  readonly label: string;
  readonly spec: string;
  readonly generatedRoutes: readonly {
    readonly method: HttpMethod;
    readonly path: string;
    readonly status: number;
    readonly note: string;
  }[];
}

export interface DeploymentMode {
  readonly id: 'onprem' | 'saas';
  readonly title: string;
  readonly subtitle: string;
  readonly command: string;
  readonly highlights: readonly string[];
  readonly architecture: readonly {
    readonly label: string;
    readonly value: string;
  }[];
}

export const MOCK_ENDPOINTS: readonly MockEndpoint[] = [
  {
    id: 'users-list',
    method: 'GET',
    path: '/api/v1/users',
    summary: 'List workspace members with pagination metadata',
    defaultStatus: 200,
    payloads: {
      200: {
        ok: true,
        data: [
          { id: 'usr_01', name: 'Aarav Mehta', role: 'admin', active: true },
          { id: 'usr_02', name: 'Zara Khan', role: 'developer', active: true },
        ],
        meta: { page: 1, total: 24, source: 'mockease-engine' },
      },
      201: { ok: true, message: 'Snapshot created', id: 'snap_92f' },
      429: { ok: false, error: 'rate_limit_exceeded', retryAfterSec: 12 },
      500: { ok: false, error: 'upstream_timeout', traceId: 'tr_991a0c' },
    },
  },
  {
    id: 'orders-create',
    method: 'POST',
    path: '/api/v1/orders',
    summary: 'Create a checkout order with dynamic total calculation',
    defaultStatus: 201,
    payloads: {
      200: { ok: true, orderId: 'ord_4410', status: 'confirmed', total: 149.0 },
      201: {
        ok: true,
        orderId: 'ord_4410',
        status: 'created',
        currency: 'USD',
        total: 149.0,
        createdAt: '2026-11-26T08:25:00Z',
      },
      429: { ok: false, error: 'too_many_requests', limit: '60/min' },
      500: { ok: false, error: 'payment_gateway_unavailable', code: 'E_GATEWAY' },
    },
  },
  {
    id: 'auth-token',
    method: 'PUT',
    path: '/api/v1/session/refresh',
    summary: 'Rotate short-lived JWT access token & claims',
    defaultStatus: 200,
    payloads: {
      200: {
        tokenType: 'Bearer',
        expiresIn: 900,
        scope: 'mocks:read mocks:write',
        rotated: true,
      },
      201: { tokenType: 'Bearer', issued: true, expiresIn: 900 },
      429: { ok: false, error: 'token_rotation_throttled' },
      500: { ok: false, error: 'signing_key_unavailable' },
    },
  },
  {
    id: 'webhook-purge',
    method: 'DELETE',
    path: '/api/v1/webhooks/wh_882',
    summary: 'Remove webhook subscription and flush queue',
    defaultStatus: 200,
    payloads: {
      200: { deleted: true, webhookId: 'wh_882', flushedEvents: 4 },
      201: { queuedForDeletion: true, webhookId: 'wh_882' },
      429: { ok: false, error: 'delete_rate_limited' },
      500: { ok: false, error: 'worker_lock_conflict' },
    },
  },
];

export const OPENAPI_SAMPLES: readonly OpenApiSample[] = [
  {
    id: 'ecommerce',
    label: 'E-Commerce API',
    spec: `openapi: 3.1.0
info:
  title: Storefront API
  version: 1.4.0
paths:
  /products:
    get:
      summary: List catalog items
  /cart/checkout:
    post:
      summary: Process cart checkout
  /orders/{id}:
    get:
      summary: Fetch order status`,
    generatedRoutes: [
      { method: 'GET', path: '/mock/products', status: 200, note: '12 seeded SKUs · 18ms' },
      { method: 'POST', path: '/mock/cart/checkout', status: 201, note: 'Order receipt · 45ms' },
      { method: 'GET', path: '/mock/orders/:id', status: 200, note: 'Dynamic :id echo' },
    ],
  },
  {
    id: 'fintech',
    label: 'Ledger & Billing',
    spec: `openapi: 3.1.0
info:
  title: Ledger Core
  version: 2.0.0
paths:
  /invoices:
    post:
      summary: Issue client invoice
  /payouts/simulate:
    put:
      summary: Trigger settlement webhook
  /accounts/{id}/balance:
    get:
      summary: Query available balance`,
    generatedRoutes: [
      { method: 'POST', path: '/mock/invoices', status: 201, note: 'Auto-generated PDF URL' },
      { method: 'PUT', path: '/mock/payouts/simulate', status: 200, note: 'Fires webhook payload' },
      { method: 'GET', path: '/mock/accounts/:id/balance', status: 200, note: 'Multi-currency JSON' },
    ],
  },
];

export const DEPLOYMENT_MODES: readonly DeploymentMode[] = [
  {
    id: 'onprem',
    title: 'On-Premise / Self-Hosted',
    subtitle: 'Run inside your own VPC, CI pipeline, or air-gapped Docker network with zero external data egress.',
    command: 'git clone https://github.com/fvrvz/mockease.git && cd mockease && docker compose up -d',
    highlights: [
      'Full Python + Vue 3 stack in one Compose file',
      'SQLite or PostgreSQL persistence with Alembic migrations',
      'Ideal for local dev, Playwright E2E, and private staging',
    ],
    architecture: [
      { label: 'Runtime', value: 'Docker / Python FastAPI' },
      { label: 'Storage', value: 'PostgreSQL / SQLite' },
      { label: 'Network', value: '100% Local / Private VPC' },
    ],
  },
  {
    id: 'saas',
    title: 'Managed Cloud SaaS',
    subtitle: 'Share live mock endpoints across frontend, mobile, and QA teams in seconds without managing servers.',
    command: 'curl -s https://mockease.byfaraaz.com/api/v1/users -H "X-Workspace: demo"',
    highlights: [
      'Instant shareable workspace URLs for distributed teams',
      'Real-time request inspector & latency/fault injection',
      'One-click OpenAPI 3.x import & team mock collections',
    ],
    architecture: [
      { label: 'Endpoint', value: 'mockease.byfaraaz.com' },
      { label: 'Collaboration', value: 'Shared Workspaces' },
      { label: 'Setup Time', value: '< 10 seconds' },
    ],
  },
];
