import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

describe('ConfirmDialog', () => {
  it('does not render when show is false', () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        show: false,
        message: 'Are you sure?',
      },
      global: {
        stubs: {
          Teleport: true,
          Transition: true,
        },
      },
    })
    expect(wrapper.find('.dialog-backdrop').exists()).toBe(false)
  })

  it('renders title, message, and default buttons when show is true', () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        show: true,
        title: 'Delete Application',
        message: 'This cannot be undone',
        confirmText: 'Delete Now',
        cancelText: 'Nevermind',
        variant: 'danger',
      },
      global: {
        stubs: {
          Teleport: true,
          Transition: true,
        },
      },
    })
    expect(wrapper.find('.dialog-backdrop').exists()).toBe(true)
    expect(wrapper.find('.dialog-title').text()).toBe('Delete Application')
    expect(wrapper.find('.dialog-message').text()).toBe('This cannot be undone')
    expect(wrapper.find('.btn--danger').text()).toContain('Delete Now')
    expect(wrapper.find('.btn--ghost').text()).toContain('Nevermind')
  })

  it('emits confirm when confirm button is clicked', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        show: true,
        message: 'Confirm action',
      },
      global: {
        stubs: {
          Teleport: true,
          Transition: true,
        },
      },
    })
    const confirmBtn = wrapper.findAll('button').find((b) => b.classes('btn--danger'))
    await confirmBtn?.trigger('click')
    expect(wrapper.emitted('confirm')).toBeTruthy()
  })

  it('emits cancel when cancel button or backdrop is clicked', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        show: true,
        message: 'Cancel action',
      },
      global: {
        stubs: {
          Teleport: true,
          Transition: true,
        },
      },
    })
    const cancelBtn = wrapper.find('.btn--ghost')
    await cancelBtn.trigger('click')
    expect(wrapper.emitted('cancel')).toBeTruthy()

    await wrapper.find('.dialog-backdrop').trigger('click')
    expect(wrapper.emitted('cancel')?.length).toBe(2)
  })

  it('shows loading state when loading prop is true', () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        show: true,
        message: 'Deleting...',
        loading: true,
      },
      global: {
        stubs: {
          Teleport: true,
          Transition: true,
        },
      },
    })
    expect(wrapper.text()).toContain('Processing...')
    const buttons = wrapper.findAll('button')
    buttons.forEach((btn) => {
      expect(btn.attributes('disabled')).toBeDefined()
    })
  })
})
