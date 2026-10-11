import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ImportSpecModal from '@/components/ImportSpecModal.vue'

describe('ImportSpecModal Component', () => {
  it('does not render when show is false', () => {
    const wrapper = mount(ImportSpecModal, {
      props: { show: false },
    })
    expect(wrapper.find('.modal-card').exists()).toBe(false)
  })

  it('renders modal when show is true with default title', () => {
    const wrapper = mount(ImportSpecModal, {
      props: { show: true },
    })
    expect(wrapper.find('.modal-card').exists()).toBe(true)
    expect(wrapper.find('.modal-title').text()).toBe('Import API Specification')
    expect(wrapper.find('.form-input').exists()).toBe(true)
  })

  it('renders customized title and subtitle when targetAppId and targetAppName are provided', () => {
    const wrapper = mount(ImportSpecModal, {
      props: {
        show: true,
        targetAppId: 'app-123',
        targetAppName: 'Billing Service',
      },
    })
    expect(wrapper.find('.modal-title').text()).toBe('Import into Application')
    expect(wrapper.find('.modal-subtitle').text()).toContain('Billing Service')
    // App Name field should be hidden when merging into existing app
    expect(wrapper.find('.form-input').exists()).toBe(false)
  })

  it('detects OpenAPI 3.x format dynamically', async () => {
    const wrapper = mount(ImportSpecModal, {
      props: { show: true },
    })
    const textarea = wrapper.find('textarea')
    await textarea.setValue('{"openapi": "3.0.0", "info": {"title": "Test"}}')

    const badge = wrapper.find('.format-badge')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe('OpenAPI 3.x')
  })

  it('detects Swagger 2.0 format dynamically', async () => {
    const wrapper = mount(ImportSpecModal, {
      props: { show: true },
    })
    const textarea = wrapper.find('textarea')
    await textarea.setValue('{"swagger": "2.0", "info": {"title": "Test"}}')

    const badge = wrapper.find('.format-badge')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe('Swagger 2.0')
  })

  it('detects Postman v2.1 format dynamically', async () => {
    const wrapper = mount(ImportSpecModal, {
      props: { show: true },
    })
    const textarea = wrapper.find('textarea')
    await textarea.setValue('{"info": {"schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"}}')

    const badge = wrapper.find('.format-badge')
    expect(badge.exists()).toBe(true)
    expect(badge.text()).toBe('Postman v2.1')
  })

  it('shows error if submitted with empty specification', async () => {
    const wrapper = mount(ImportSpecModal, {
      props: { show: true },
    })
    const buttons = wrapper.findAll('button')
    const submitBtn = buttons.find((b) => b.text().includes('Import Specification'))
    expect(submitBtn).toBeDefined()
    // Submit button is disabled when empty
    expect(submitBtn!.attributes('disabled')).toBeDefined()
  })

  it('emits imported event with spec and custom app name on valid submit', async () => {
    const wrapper = mount(ImportSpecModal, {
      props: { show: true },
    })
    const nameInput = wrapper.find('.form-input')
    await nameInput.setValue('Custom API')

    const textarea = wrapper.find('textarea')
    await textarea.setValue('openapi: 3.0.3\ninfo:\n  title: Test')

    const buttons = wrapper.findAll('button')
    const submitBtn = buttons.find((b) => b.text().includes('Import Specification'))
    await submitBtn!.trigger('click')

    expect(wrapper.emitted('imported')).toBeTruthy()
    const emittedData = wrapper.emitted('imported')![0]![0] as {
      spec: string
      name?: string
      targetAppId?: string
    }
    expect(emittedData.spec).toContain('openapi: 3.0.3')
    expect(emittedData.name).toBe('Custom API')
    expect(emittedData.targetAppId).toBeUndefined()
  })

  it('emits close event when close button or cancel is clicked', async () => {
    const wrapper = mount(ImportSpecModal, {
      props: { show: true },
    })
    const closeBtn = wrapper.find('.btn-close')
    await closeBtn.trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()

    const cancelBtn = wrapper.findAll('button').find((b) => b.text() === 'Cancel')
    await cancelBtn!.trigger('click')
    expect(wrapper.emitted('close')!.length).toBe(2)
  })

  it('handles drag over and leave events on dropzone', async () => {
    const wrapper = mount(ImportSpecModal, {
      props: { show: true },
    })
    const dropzone = wrapper.find('.dropzone')
    await dropzone.trigger('dragover')
    expect(dropzone.classes()).toContain('dropzone--active')

    await dropzone.trigger('dragleave')
    expect(dropzone.classes()).not.toContain('dropzone--active')
  })

  it('handles file input change and reads text via FileReader', async () => {
    const wrapper = mount(ImportSpecModal, {
      props: { show: true },
    })

    const file = new File(['openapi: 3.0.0\ninfo:\n  title: File API'], 'petstore-api.yaml', {
      type: 'text/yaml',
    })

    // Mock FileReader
    const originalFileReader = window.FileReader
    class MockFileReader {
      onload: ((e: { target: { result: string } }) => void) | null = null
      onerror: (() => void) | null = null
      readAsText() {
        if (this.onload) {
          this.onload({ target: { result: 'openapi: 3.0.0\ninfo:\n  title: File API' } })
        }
      }
    }
    window.FileReader = MockFileReader as unknown as typeof FileReader

    try {
      const input = wrapper.find<HTMLInputElement>('input[type="file"]')
      Object.defineProperty(input.element, 'files', {
        value: [file],
      })
      await input.trigger('change')

      expect(wrapper.find('.dropzone__filename').text()).toContain('petstore-api.yaml')
      expect(wrapper.find<HTMLInputElement>('.form-input').element.value).toBe('Petstore api')
      expect(wrapper.find<HTMLTextAreaElement>('textarea').element.value).toContain('File API')
    } finally {
      window.FileReader = originalFileReader
    }
  })

  it('handles drop event with file', async () => {
    const wrapper = mount(ImportSpecModal, {
      props: { show: true },
    })

    const file = new File(['{"openapi": "3.0.0"}'], 'spec.json', { type: 'application/json' })

    const originalFileReader = window.FileReader
    class MockFileReader {
      onload: ((e: { target: { result: string } }) => void) | null = null
      onerror: (() => void) | null = null
      readAsText() {
        if (this.onload) {
          this.onload({ target: { result: '{"openapi": "3.0.0"}' } })
        }
      }
    }
    window.FileReader = MockFileReader as unknown as typeof FileReader

    try {
      const dropzone = wrapper.find('.dropzone')
      await dropzone.trigger('drop', {
        dataTransfer: {
          files: [file],
        },
      })
      expect(wrapper.find('.dropzone__filename').text()).toContain('spec.json')
    } finally {
      window.FileReader = originalFileReader
    }
  })
})

