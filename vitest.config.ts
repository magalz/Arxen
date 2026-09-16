import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    include: ['apps/web/src/**/*.test.{ts,tsx}', 'packages/*/src/**/*.test.{ts,tsx}'],
    setupFiles: ['tests/web/setup.ts'],
    allowOnly: !process.env.CI,
    reporters: ['default', 'junit'],
    outputFile: { junit: 'test-results/web/junit.xml' },
    coverage: {
      provider: 'v8',
      include: ['apps/web/src/**/*.{ts,tsx}', 'packages/*/src/**/*.{ts,tsx}'],
      exclude: ['**/*.test.{ts,tsx}', '**/*.d.ts', 'apps/web/src/main.tsx'],
      reporter: ['text', 'lcov', 'json-summary', 'html'],
      reportsDirectory: 'coverage/web',
      thresholds: { lines: 85, branches: 85, functions: 85, statements: 85 },
    },
  },
});
