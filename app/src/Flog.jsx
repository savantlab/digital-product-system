import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import './Flog.css'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'

const PLACEHOLDER_ARTICLES = [
  {
    id: 1,
    slug: 'decoding-the-deception',
    title: 'Decoding the Deception: How Academic Fraud Became a Movement',
    excerpt: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.',
    published_at: '2024-01-15',
    tags: ['Academic Fraud', 'Maps of Meaning', 'Harvard']
  },
  {
    id: 2,
    slug: 'the-pipeline-problem',
    title: 'The Pipeline Problem: From Lecture Hall to Radicalization',
    excerpt: 'Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit.',
    published_at: '2024-01-22',
    tags: ['Radicalization', 'Ideology', 'Culture War']
  },
  {
    id: 3,
    slug: 'fabricated-symbolism',
    title: 'Fabricated Symbolism: Peterson\'s Imagined Heraldry and Made-Up Meanings',
    excerpt: 'Peterson severely lacks actual heraldry examples in Maps of Meaning. Instead, he makes up his own imagined symbolism with ambiguated meanings for Osiris, yin-yang, and other ancient symbols—never admitting he derived them incorrectly. This is pretend play masquerading as scholarship.',
    published_at: '2024-02-05',
    tags: ['Maps of Meaning', 'Symbolism', 'Osiris', 'Yin-Yang', 'Fraud']
  },
  {
    id: 4,
    slug: 'lexical-alchemy',
    title: 'Lexical Alchemy: The Art of Academic Word Salad',
    excerpt: 'Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae.',
    published_at: '2024-02-12',
    tags: ['Language Games', 'Rhetoric', 'Deception']
  },
  {
    id: 5,
    slug: 'the-hero-myth-weaponized',
    title: 'The Hero Myth Weaponized: Jung, Campbell, and Mass Manipulation',
    excerpt: 'Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt. Neque porro quisquam est, qui dolorem.',
    published_at: '2024-02-18',
    tags: ['Mythology', 'Psychology', 'Manipulation']
  },
  {
    id: 6,
    slug: 'follow-the-money',
    title: 'Follow the Money: How Fraud Became a Fortune',
    excerpt: 'Quis autem vel eum iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum qui dolorem eum fugiat quo voluptas nulla pariatur. At vero eos et accusamus.',
    published_at: '2024-03-03',
    tags: ['Economics', 'Grift', 'Platform Building']
  },
  {
    id: 7,
    slug: 'reputation-destruction-playbook',
    title: 'The Reputation Destruction Playbook: Peterson\'s Defense Strategy',
    excerpt: 'Et harum quidem rerum facilis est et expedita distinctio. Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere possimus, omnis voluptas.',
    published_at: '2024-03-17',
    tags: ['Strategy', 'Defense Mechanisms', 'Female Sociopathy']
  }
]

export default function Flog() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch articles from API
    fetch(`${API_BASE}/api/flog/articles`)
      .then(res => res.json())
      .then(data => {
        if (data.ok && data.articles.length > 0) {
          setArticles(data.articles)
        } else {
          // Use placeholder articles if API returns no content
          setArticles(PLACEHOLDER_ARTICLES)
        }
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load articles:', err)
        // Use placeholder articles on error
        setArticles(PLACEHOLDER_ARTICLES)
        setLoading(false)
      })
  }, [])

  return (
    <div className="flog-page">
      <Link to="/contents" className="back-to-contents">
        ← Back to Contents
      </Link>

      <header className="flog-header">
        <h1>The Flog</h1>
        <p className="flog-tagline">Fraud Blog: Exposing Academic Deception</p>
        <p className="flog-description">
          Documenting Jordan Peterson's academic fraud at Harvard, the Maps of Meaning deception, 
          and the ideological pipeline from fraudulent scholarship to extremist radicalization.
        </p>
      </header>

      <div className="articles-container">
        {loading ? (
          <p className="loading-message">Loading articles...</p>
        ) : articles.length === 0 ? (
          <div className="no-articles">
            <p>Articles coming soon.</p>
            <p className="coming-soon-message">
              We're documenting the fraud, lies, and deception. Check back soon for in-depth analysis 
              of Peterson's academic misconduct and its consequences.
            </p>
          </div>
        ) : (
          <div className="articles-grid">
            {articles.map(article => (
              <article key={article.id} className="article-card">
                <div className="article-meta">
                  <span className="article-date">{new Date(article.published_at).toLocaleDateString()}</span>
                  {article.tags && (
                    <div className="article-tags">
                      {article.tags.map((tag, i) => (
                        <span key={i} className="tag">{tag}</span>
                      ))}
                    </div>
                  )}
                </div>
                <h2 className="article-title">{article.title}</h2>
                <p className="article-excerpt">{article.excerpt}</p>
                <a href={`/flog/${article.slug}`} className="read-more">
                  Read Full Article →
                </a>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
