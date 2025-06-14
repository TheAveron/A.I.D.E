import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './assets/css/index.css'
import App from './App/App'

createRoot(document.getElementById('body')!).render(
    <StrictMode>
        <App />
    </StrictMode>,
)
