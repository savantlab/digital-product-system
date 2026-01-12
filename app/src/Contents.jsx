import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import TOUModal from './components/TOUModal'
import { methodologySlides } from './sections/methodology'
import { textExamplesSlides } from './sections/textExamples'
import { discourseAnalysisSlides } from './sections/discourseAnalysis'
import { implicationsSlides } from './sections/implications'
import './Contents.css'

// Import App to count introduction slides
import { useState as useAppState } from 'react'

const sections = [
  {
    id: 'introduction',
    title: 'Introduction',
    description: 'Overview of the analysis and research question',
    slides: 16, // Note: Counted from App.jsx introductionSlides array
    path: '/section/introduction'
  },
  {
    id: 'methodology',
    title: 'Methodology Deep Dive',
    description: 'Detailed walkthrough of NLP techniques and analysis methods',
    slides: methodologySlides.length,
    path: '/section/methodology'
  },
  {
    id: 'text-examples',
    title: 'Rhetorical Excerpts',
    description: 'Examining supremacist rhetoric in both texts',
    slides: textExamplesSlides.length,
    path: '/section/text-examples'
  },
  {
    id: 'discourse-analysis',
    title: 'Discourse Analysis',
    description: 'Rhetorical patterns and speech act theory',
    slides: discourseAnalysisSlides.length,
    path: '/section/discourse-analysis'
  },
  {
    id: 'implications',
    title: 'Implications & Ethics',
    description: 'Understanding radicalization and responsible research',
    slides: implicationsSlides.length,
    path: '/section/implications'
  }
]

export default function Contents() {
  const [showTOU, setShowTOU] = useState(false)

  useEffect(() => {
    // Check if user has accepted TOU before
    const hasAcceptedTOU = localStorage.getItem('tou_accepted')
    if (!hasAcceptedTOU) {
      setShowTOU(true)
    }
  }, [])

  const handleAcceptTOU = () => {
    localStorage.setItem('tou_accepted', 'true')
    localStorage.setItem('tou_accepted_date', new Date().toISOString())
    setShowTOU(false)
  }

  return (
    <>
      {showTOU && <TOUModal onAccept={handleAcceptTOU} />}
      <div className="contents-page">
        <header className="contents-header">
        <h1>Parallel Critiques</h1>
        <p className="subtitle">Analyzing Rhetorical Extremism</p>
        <p className="course-description">
          A structured analysis of textual and ideological overlap between academic political critique 
          and extremist manifestos, using computational linguistics and rhetorical analysis.
        </p>
      </header>

      <div className="sections-grid">
        {sections.map((section) => (
          <div key={section.id} className={`section-card ${section.comingSoon ? 'coming-soon' : ''}`}>
            <div className="section-number">{sections.indexOf(section) + 1}</div>
            <h2>{section.title}</h2>
            <p className="section-description">{section.description}</p>
            <div className="section-meta">
              <span className="slide-count">{section.slides} slides</span>
            </div>
            {section.comingSoon ? (
              <div className="coming-soon-badge">Coming Soon</div>
            ) : (
              <Link to={section.path} className="section-link">
                Start Section →
              </Link>
            )}
          </div>
        ))}
      </div>

      <footer className="contents-footer">
        <p>Navigate through sections sequentially or jump to specific topics.</p>
      </footer>

      {/* The Flog Jumbotron */}
      <div className="flog-jumbotron">
        <div className="flog-jumbotron-content">
          <h2 className="flog-title">The Flog</h2>
          <p className="flog-subtitle">Fraud Blog: Exposing Academic Deception</p>
          <p className="flog-text">
            Deep dives into Jordan Peterson's academic fraud at Harvard, the Maps of Meaning deception, 
            and how fraudulent scholarship creates the ideological scaffolding for extremism.
          </p>
          <Link to="/flog" className="flog-cta">
            Read The Flog →
          </Link>
        </div>
      </div>
      </div>
    </>
  )
}
