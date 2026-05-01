import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

import { ThemeProvider, CssBaseline, createTheme } from '@mui/material'

const theme = createTheme({
  palette: {
    mode: 'light', // change to 'dark' anytime later
    primary: {
      main: '#1976d2',
    },
  },
})

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </StrictMode>,
)