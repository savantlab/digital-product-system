import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import App from './App'
import Contents from './Contents'
import Flog from './Flog'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/contents" replace />} />
        <Route path="/contents" element={<Contents />} />
        <Route path="/section/introduction" element={<App section="introduction" />} />
        <Route path="/section/methodology" element={<App section="methodology" />} />
        <Route path="/section/text-examples" element={<App section="text-examples" />} />
        <Route path="/section/discourse-analysis" element={<App section="discourse-analysis" />} />
        <Route path="/section/implications" element={<App section="implications" />} />
        <Route path="/flog" element={<Flog />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)
