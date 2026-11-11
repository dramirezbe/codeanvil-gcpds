import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import '@fontsource-variable/dm-sans'
import '@fontsource/dm-mono/latin-400.css'
import '@fontsource/dm-mono/latin-500.css'
import '@fontsource-variable/space-grotesk'
import './styles/tokens.css'
import './styles/workspace.css'

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>)
