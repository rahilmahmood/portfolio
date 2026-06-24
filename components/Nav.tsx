'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

// ── Update this with your actual resume URL ──────────────────
const RESUME_URL = '/resume.pdf'
const LINKEDIN_URL = 'https://linkedin.com/in/yourhandle'

export default function Nav() {
  const path = usePathname()

  // Don't render the portfolio nav inside the studio
  if (path.startsWith('/studio')) return null

  return (
    <nav className="nav">
      <div className="nav-inner">
        <Link href="/" className="nav-name">
          Rahil Mahmood {/* ← Change this */}
        </Link>
        <div className="nav-links">
          <Link href="/projects" className="nav-link" aria-current={path.startsWith('/projects') ? 'page' : undefined}>
            Projects
          </Link>
          <Link href="/about" className="nav-link" aria-current={path === '/about' ? 'page' : undefined}>
            About
          </Link>
          <a href={RESUME_URL} target="_blank" rel="noopener noreferrer" className="nav-cta">
            Resume ↗
          </a>
        </div>
      </div>
    </nav>
  )
}
