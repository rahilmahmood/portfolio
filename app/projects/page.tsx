import Nav from '@/components/Nav'
import ProjectCard from '@/components/ProjectCard'
import { client } from '@/sanity/lib/client'
import { projectsQuery } from '@/sanity/lib/queries'
import type { ProjectStub } from '@/types'

export const revalidate = 60

export const metadata = {
  title: 'Projects — Rahil Mahmood',
}

export default async function ProjectsPage() {
  const projects = await client.fetch<ProjectStub[]>(projectsQuery)

  return (
    <>
      <Nav />
      <main className="page">
        <div className="container" style={{ paddingTop: 72 }}>
          <p className="label" style={{ marginBottom: 12 }}>Work</p>
          <h1 style={{ fontSize: 'clamp(32px, 5vw, 52px)', marginBottom: 56 }}>All Projects</h1>

          {projects.length === 0 ? (
            <p style={{ color: 'var(--muted)', fontSize: 15 }}>
              No projects yet — add one in the{' '}
              <a href="/studio" style={{ color: 'var(--accent)' }}>CMS studio</a>.
            </p>
          ) : (
            <div className="grid-2">
              {projects.map((p) => <ProjectCard key={p._id} project={p} />)}
            </div>
          )}
        </div>
      </main>
      <footer className="footer">
        <div className="container">Built from scratch · Hosted on Vercel</div>
      </footer>
    </>
  )
}
