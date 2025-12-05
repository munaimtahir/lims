import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Build configuration
  build: {
    outDir: 'dist',
    sourcemap: false, // Disable sourcemaps in production for security
    minify: 'esbuild',
  },
})
