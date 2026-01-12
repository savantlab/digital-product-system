import { useState, useEffect } from 'react'
import './TOUModal.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'

export default function TOUModal({ onAccept }) {
  const [agreed, setAgreed] = useState(false)
  const [touData, setTouData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Fetch active TOU content from API
    fetch(`${API_BASE}/api/tou`)
      .then(res => res.json())
      .then(data => {
        if (data.ok) {
          setTouData(data.data)
        } else {
          setError(data.error || 'Failed to load Terms of Use')
        }
        setLoading(false)
      })
      .catch(err => {
        setError('Failed to load Terms of Use')
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="tou-overlay">
        <div className="tou-modal">
          <h1>Terms of Use</h1>
          <div className="tou-content">
            <p>Loading Terms of Use...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="tou-overlay">
        <div className="tou-modal">
          <h1>Terms of Use</h1>
          <div className="tou-content">
            <p style={{color: 'red'}}>Error: {error}</p>
            <button className="accept-button" onClick={onAccept}>
              Continue Anyway
            </button>
          </div>
        </div>
      </div>
    )
  }

  const content = touData?.content || {}
  const sections = content.sections || []
  const agreementText = content.agreement_text || 'I agree to the Terms of Use'

  return (
    <div className="tou-overlay">
      <div className="tou-modal">
        <h1>Terms of Use</h1>
        <div className="tou-content">
          {sections.map((section, index) => (
            <div key={index}>
              <h2>{section.title}</h2>
              {section.content.split('\n').map((para, pIndex) => {
                // Check if it's a bullet list
                if (para.trim().startsWith('•')) {
                  return <li key={`${index}-${pIndex}`}>{para.trim().substring(1).trim()}</li>
                }
                // Check if previous or next line is a bullet (for wrapping in ul)
                const lines = section.content.split('\n')
                const prevLine = lines[pIndex - 1]
                const nextLine = lines[pIndex + 1]
                
                if (para.trim()) {
                  if (para.includes('<strong>')) {
                    return (
                      <p key={`${index}-${pIndex}`}>
                        <strong>{para.replace(/<\/?strong>/g, '')}</strong>
                      </p>
                    )
                  }
                  if (para.includes('<a ')) {
                    // Simple email link parsing
                    const match = para.match(/contact: (.+@.+\..+)/)
                    if (match) {
                      return (
                        <p key={`${index}-${pIndex}`}>
                          For questions about these terms, contact: <a href={`mailto:${match[1]}`}>{match[1]}</a>
                        </p>
                      )
                    }
                  }
                  return <p key={`${index}-${pIndex}`}>{para}</p>
                }
                return null
              }).filter(Boolean).map((element, idx, arr) => {
                // Wrap consecutive <li> elements in <ul>
                if (element.type === 'li') {
                  const prevIsLi = idx > 0 && arr[idx - 1]?.type === 'li'
                  const nextIsLi = idx < arr.length - 1 && arr[idx + 1]?.type === 'li'
                  
                  if (!prevIsLi && nextIsLi) {
                    // Start of list
                    const listItems = []
                    for (let i = idx; i < arr.length && arr[i].type === 'li'; i++) {
                      listItems.push(arr[i])
                    }
                    return <ul key={`ul-${index}-${idx}`}>{listItems}</ul>
                  } else if (!prevIsLi && !nextIsLi) {
                    // Single item list
                    return <ul key={`ul-${index}-${idx}`}>{element}</ul>
                  }
                  // Skip items already wrapped
                  return null
                }
                return element
              }).filter(Boolean)}
            </div>
          ))}

          <div className="agreement-section">
            <label className="checkbox-label">
              <input 
                type="checkbox" 
                checked={agreed} 
                onChange={(e) => setAgreed(e.target.checked)}
              />
              <span>
                {agreementText}
              </span>
            </label>
          </div>

          <button 
            className="accept-button" 
            disabled={!agreed}
            onClick={onAccept}
          >
            Accept and Continue
          </button>
        </div>
      </div>
    </div>
  )
}
