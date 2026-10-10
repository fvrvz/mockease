import { test, expect } from '@playwright/test'

test.describe('MockEase API Integration Tests', () => {
  const testUser = {
    email: `playwright_${Date.now()}@mockease.dev`,
    username: `pw_user_${Date.now()}`,
    password: 'Password123!',
  }

  let authToken = ''
  let createdAppSlug = ''
  let createdAppId = ''
  let createdCtrlId = ''

  test('Backend Health Endpoint responds with ok', async ({ request }) => {
    const res = await request.get('http://localhost:8000/health')
    expect(res.status()).toBe(200)
    const body = await res.json()
    expect(body.status).toBe('ok')
    expect(body.version).toBe('0.1.0')
  })

  test('Registers and logs in a new user', async ({ request }) => {
    // Register
    const regRes = await request.post('http://localhost:8000/api/v1/auth/register', {
      data: testUser,
    })
    expect(regRes.status()).toBe(201)
    const regData = await regRes.json()
    expect(regData.email).toBe(testUser.email)
    expect(regData.username).toBe(testUser.username)

    // Login
    const loginRes = await request.post('http://localhost:8000/api/v1/auth/login', {
      data: {
        email: testUser.email,
        password: testUser.password,
      },
    })
    expect(loginRes.status()).toBe(200)
    const loginData = await loginRes.json()
    expect(loginData.access_token).toBeDefined()
    authToken = loginData.access_token

    // Verify /me
    const meRes = await request.get('http://localhost:8000/api/v1/auth/me', {
      headers: { Authorization: `Bearer ${authToken}` },
    })
    expect(meRes.status()).toBe(200)
    const meData = await meRes.json()
    expect(meData.username).toBe(testUser.username)
  })

  test('Creates application, controller, and endpoint', async ({ request }) => {
    const headers = { Authorization: `Bearer ${authToken}` }

    // 1. Create Application
    const appRes = await request.post('http://localhost:8000/api/v1/applications', {
      headers,
      data: {
        name: 'Playwright API App',
        description: 'End to end tested mock application',
      },
    })
    expect(appRes.status()).toBe(201)
    const appData = await appRes.json()
    createdAppId = appData.id
    createdAppSlug = appData.slug
    expect(createdAppSlug).toContain('playwright-api-app')

    // 2. Create Controller
    const ctrlRes = await request.post(`http://localhost:8000/api/v1/applications/${createdAppId}/controllers`, {
      headers,
      data: {
        name: 'Orders',
        description: 'Order management controller',
      },
    })
    expect(ctrlRes.status()).toBe(201)
    const ctrlData = await ctrlRes.json()
    createdCtrlId = ctrlData.id

    // 3. Create Mock Endpoint
    const epRes = await request.post(`http://localhost:8000/api/v1/controllers/${createdCtrlId}/endpoints`, {
      headers,
      data: {
        name: 'Get Order by ID',
        method: 'GET',
        path: '/orders/{order_id}',
        response_status: 200,
        response_body: {
          order_id: '{{request.path.order_id}}',
          tracking: '{{uuid}}',
          status: 'shipped',
        },
        response_body_type: 'json',
        response_delay_ms: 0,
        response_headers: [
          { name: 'X-Mock-Engine', value: 'MockEase-Playwright' },
        ],
      },
    })
    expect(epRes.status()).toBe(201)
  })

  test('Directly invokes mock runtime endpoint with dynamic templating', async ({ request }) => {
    const mockUrl = `http://localhost:8000/mock/${createdAppSlug}/orders/98765`
    const res = await request.get(mockUrl)
    expect(res.status()).toBe(200)
    expect(res.headers()['x-mock-engine']).toBe('MockEase-Playwright')

    const body = await res.json()
    expect(body.order_id).toBe('98765')
    expect(body.status).toBe('shipped')
    expect(body.tracking).toMatch(/^[0-9a-f-]{36}$/)
  })
})
