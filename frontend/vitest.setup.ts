import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock the scrollIntoView which is not implemented in jsdom
window.HTMLElement.prototype.scrollIntoView = vi.fn()
