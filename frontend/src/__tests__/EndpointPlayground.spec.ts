import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import EndpointPlayground from '@/components/EndpointPlayground.vue'
import type { ApiEndpoint } from '@/types/endpoint'

const mockEndpoint: ApiEndpoint = {
  id: 'ep-123',
  controller_id: 'ctrl-1',
  name: 'Get User By ID',
  description: null,
  method: 'GET',
  path: '/users/{id}',
  is_enabled: true,
  auth_inherit: 'inherit',
  response_status: 200,
  response_body: { id: 1, name: 'John Doe' },
  response_body_type: 'json',
  response_delay_ms: 0,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  request_params: [
    {
      id: 'p-1',
      param_type: 'query',
      name: 'include_details',
      value_type: 'boolean',
      required: false,
      default_val: 'true',
    },
  ],
}

const mockPostEndpoint: ApiEndpoint = {
  id: 'ep-post',
  controller_id: 'ctrl-1',
  name: 'Create User',
  description: null,
  method: 'POST',
  path: '/users',
  is_enabled: true,
  auth_inherit: 'inherit',
  response_status: 201,
  response_body: { id: 2, name: 'Jane Doe' },
  response_body_type: 'json',
  response_delay_ms: 0,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
}

describe('EndpointPlayground', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    })
  })

  it('renders the request bar and extracts path variables', () => {
    const wrapper = mount(EndpointPlayground, {
      props: {
        endpoint: mockEndpoint,
        appSlug: 'demo-api',
      },
    })

    expect(wrapper.text()).toContain('GET')
    expect(wrapper.text()).toContain('Path Variables')
    expect(wrapper.text()).toContain('id')

    const keyInput = wrapper.find('.kv-key').element as HTMLInputElement
    expect(keyInput.value).toBe('include_details')
  })

  it('generates multi-language code snippets accurately', async () => {
    const wrapper = mount(EndpointPlayground, {
      props: {
        endpoint: mockEndpoint,
        appSlug: 'demo-api',
      },
    })

    const tabs = wrapper.findAll('.nav-tab')
    const snippetsTab = tabs.find((t) => t.text().includes('Code Snippets'))
    expect(snippetsTab).toBeDefined()
    await snippetsTab?.trigger('click')

    expect(wrapper.text()).toContain('cURL (CLI)')
    expect(wrapper.text()).toContain('curl -X GET')
    expect(wrapper.text()).toContain('/mock/demo-api/users/{id}')

    const langTabs = wrapper.findAll('.snip-tab')
    const fetchTab = langTabs.find((t) => t.text().includes('Fetch'))
    await fetchTab?.trigger('click')
    expect(wrapper.text()).toContain('await fetch(')

    const axiosTab = langTabs.find((t) => t.text().includes('Axios'))
    await axiosTab?.trigger('click')
    expect(wrapper.text()).toContain('axios.get(')

    const pyTab = langTabs.find((t) => t.text().includes('Python'))
    await pyTab?.trigger('click')
    expect(wrapper.text()).toContain('requests.get(')
  })

  it('copies code snippet to clipboard and gives feedback', async () => {
    const wrapper = mount(EndpointPlayground, {
      props: {
        endpoint: mockEndpoint,
        appSlug: 'demo-api',
      },
    })

    const snippetsTab = wrapper.findAll('.nav-tab').find((t) => t.text().includes('Code Snippets'))
    await snippetsTab?.trigger('click')

    const copyBtn = wrapper.find('.btn-copy-snip')
    expect(copyBtn.exists()).toBe(true)
    await copyBtn.trigger('click')

    expect(navigator.clipboard.writeText).toHaveBeenCalled()
    expect(wrapper.text()).toContain('Copied to clipboard!')
  })

  it('allows adding and removing query parameters and headers', async () => {
    const wrapper = mount(EndpointPlayground, {
      props: {
        endpoint: mockEndpoint,
        appSlug: 'demo-api',
      },
    })

    const addQueryBtn = wrapper.findAll('button').find((b) => b.text().includes('+ Add Query Param'))
    await addQueryBtn?.trigger('click')

    const addHeaderBtn = wrapper.findAll('button').find((b) => b.text().includes('+ Add Header'))
    await addHeaderBtn?.trigger('click')

    const delBtns = wrapper.findAll('.btn-del')
    expect(delBtns.length).toBeGreaterThanOrEqual(2)
    await delBtns[0]?.trigger('click')
  })

  it('handles POST requests with request body editing and formatting', async () => {
    const wrapper = mount(EndpointPlayground, {
      props: {
        endpoint: mockPostEndpoint,
        appSlug: 'demo-api',
      },
    })

    expect(wrapper.text()).toContain('Request Body (JSON)')
    const bodyArea = wrapper.find('.body-area')
    expect(bodyArea.exists()).toBe(true)

    // Set unformatted JSON
    await bodyArea.setValue('{"name":"Alice","age":30}')
    const formatBtn = wrapper.findAll('button').find((b) => b.text().includes('Format JSON'))
    await formatBtn?.trigger('click')

    expect((bodyArea.element as HTMLTextAreaElement).value).toContain('"name": "Alice"')

    // Test invalid JSON formatting
    await bodyArea.setValue('{"bad_json')
    await formatBtn?.trigger('click')
    expect(wrapper.find('.error-banner').exists()).toBe(true)
  })

  it('executes a live mock request and renders response details', async () => {
    const mockResponse = {
      status: 200,
      statusText: 'OK',
      headers: new Headers({ 'content-type': 'application/json', 'x-mockease': 'true' }),
      text: vi.fn().mockResolvedValue(JSON.stringify({ id: 1, name: 'John Doe' })),
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(mockResponse))

    const wrapper = mount(EndpointPlayground, {
      props: {
        endpoint: mockEndpoint,
        appSlug: 'demo-api',
      },
    })

    const sendBtn = wrapper.find('.btn-send')
    expect(sendBtn.exists()).toBe(true)
    await sendBtn.trigger('click')

    await wrapper.vm.$nextTick()
    await new Promise((resolve) => setTimeout(resolve, 50))

    expect(wrapper.text()).toContain('200 OK')
    expect(wrapper.text()).toContain('John Doe')

    // Switch to response headers subtab
    const resTabs = wrapper.findAll('.res-tab')
    const headersTab = resTabs.find((t) => t.text().includes('Headers'))
    await headersTab?.trigger('click')
    expect(wrapper.text()).toContain('x-mockease')
    expect(wrapper.text()).toContain('true')

    // Click Copy Body button
    const copyBodyBtn = wrapper.findAll('button').find((b) => b.text().includes('Copy Body'))
    await copyBodyBtn?.trigger('click')
    expect(navigator.clipboard.writeText).toHaveBeenCalled()
  })

  it('handles network failure gracefully', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Connection refused')))

    const wrapper = mount(EndpointPlayground, {
      props: {
        endpoint: mockEndpoint,
        appSlug: 'demo-api',
      },
    })

    const sendBtn = wrapper.find('.btn-send')
    await sendBtn.trigger('click')

    await wrapper.vm.$nextTick()
    await new Promise((resolve) => setTimeout(resolve, 50))

    expect(wrapper.text()).toContain('Network Error')
    expect(wrapper.text()).toContain('Connection refused')
  })
})
