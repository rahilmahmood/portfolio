import Link from 'next/link'
import Nav from '@/components/Nav'
import ProjectCard from '@/components/ProjectCard'
import { client } from '@/sanity/lib/client'
import { featuredProjectsQuery } from '@/sanity/lib/queries'
import type { ProjectStub } from '@/types'

export const revalidate = 60

// ── Edit these to match your real info ───────────────────────
const LINKEDIN_URL = 'https://www.linkedin.com/in/rahilmahmood/'
const RESUME_URL = '/resume.pdf'

const CURRENTLY = [
  { label: 'Racing', text: 'Frame Lead, Longhorn Racing Electric — FSAE EV chassis design' },
  { label: 'Research', text: 'Robotics engineer at Seanergy.AI — autonomous warehouse systems' },
  { label: 'Personal', text: 'Autonomous person-tracking camera using real-time computer vision' },
]

export default async function HomePage() {
  const featured = await client.fetch<ProjectStub[]>(featuredProjectsQuery)

  return (
    <>
      <Nav />
      <main className="page">
        {/* Hero */}
        <section style={{ padding: '88px 0 0' }}>
          <div className="container">
            <p className="label" style={{ marginBottom: 28 }}>Mechanical · Electrical · Robotics</p>
            <h1 style={{ fontSize: 'clamp(44px, 7vw, 80px)', marginBottom: 24, maxWidth: 760 }}>
              Building hardware<br />
              that moves, senses,<br />
              <span style={{ borderBottom: '3px solid var(--accent)', paddingBottom: 3 }}>
                and thinks.
              </span>
            </h1>
            <p style={{ fontSize: 17, color: 'var(--muted)', maxWidth: 460, lineHeight: 1.65, marginBottom: 40 }}>
              Engineering student at UT Austin — racing frames, autonomous cameras, and real robotics applications.
            </p>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              <a href={RESUME_URL} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                Resume ↗
              </a>
              <Link href="/projects" className="btn">View Projects</Link>
              <a href={LINKEDIN_URL} target="_blank" rel="noopener noreferrer" className="btn">
                LinkedIn ↗
              </a>
            </div>
          </div>
        </section>

        {/* Currently */}
        <div className="focus-strip">
          <div className="container">
            <p className="label" style={{ marginBottom: 28 }}>Currently</p>
            <div className="focus-grid">
              {CURRENTLY.map(({ label, text }) => (
                <div key={label}>
                  <div className="focus-item-label">{label}</div>
                  <div style={{ fontSize: 14, lineHeight: 1.65 }}>{text}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Featured projects */}
        {featured.length > 0 && (
          <section>
            <div className="container">
              <p className="label" style={{ marginBottom: 36 }}>Featured Projects</p>
              <div className="grid-2">
                {featured.map((p) => <ProjectCard key={p._id} project={p} />)}
              </div>
              <div style={{ marginTop: 36, textAlign: 'center' }}>
                <Link href="/projects" className="btn">View all projects →</Link>
              </div>
            </div>
          </section>
        )}
      </main>

      <footer className="footer">
        <div className="container">Built from scratch · Hosted on Vercel</div>
      </footer>
    </>
  )
}
