import { readFileSync } from 'node:fs'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const project = readFileSync(new URL('../../../../pyproject.toml', import.meta.url), 'utf8')
const version = project.match(/^version = "([^"]+)"$/m)?.[1]
if (!version) throw new Error('Missing project version in pyproject.toml')

export default defineConfig({
  plugins: [react()],
  base: './',
  define: { __CODEANVIL_VERSION__: JSON.stringify(version) },
})
