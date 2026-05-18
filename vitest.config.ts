import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './frontend/src/test-setup.ts',
    include: ['frontend/src/tests/**/*.test.{ts,tsx}'],
    exclude: ['frontend/e2e/**', 'node_modules/**'],
  },
})
