import { notFound } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { PortableText } from '@portabletext/react'
import Nav from '@/components/Nav'
import { client } from '@/sanity/lib/client'
import { projectBySlugQuery, projectSlugsQuery } from '@/sanity/lib/queries'
import { urlFor } from '@/sanity/lib/image'
import type { Project, SanityImage } from '@/types'

export const revalidate = 60

export async function generateStaticParams() {
  const slugs = await client.fetch<{ slug: string }[]>(projectSlugsQuery)
  return slugs.map(({ slug }) => ({ slug }))
}

export async function generateMetadata({ params }: { params: { slug: string } }) {
  const project = await client.fetch<Project>(projectBySlugQuery, { slug: params.slug })
  return { title: project ? `${project.title} — Your Name` : 'Project' }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
}

const ptComponents = {
  block: {
    normal: ({ children }: any) => <p>{children}</p>,
  },
}

const CASE_SECTIONS: { key: keyof Project; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'problemGoal', label: 'Problem / Goal' },
  { key: 'whatIBuilt', label: 'What I Built' },
  { key: 'engineeringDecisions', label: 'Engineering Decisions' },
  { key: 'results', label: 'Results' },
  { key: 'nextSteps', label: 'Next Steps' },
]

export default async function ProjectPage({ params }: { params: { slug: string } }) {
  const project = await client.fetch<Project>(projectBySlugQuery, { slug: params.slug })
  if (!project) notFound()

  return (
    <>
      <Nav />
      <main className="page">
        {/* Hero image */}
        {project.heroImage ? (
          <Image
            src={urlFor(project.heroImage).width(1800).height(771).url()}
            alt={project.heroImage.alt ?? project.title}
            width={1800}
            height={771}
            className="project-hero"
            priority
          />
        ) : (
          <div className="project-hero" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span className="label" style={{ opacity: 0.4 }}>add a hero image in the CMS</span>
          </div>
        )}

        <div className="container">
          <Link href="/projects" className="back-link">← All Projects</Link>

          {/* Meta row */}
          <div className="project-meta">
            <span className="tag tag-accent">{project.category}</span>
            {project.date && (
              <span className="project-date">{formatDate(project.date)}</span>
            )}
            {project.tools?.map((t) => <span key={t} className="tag">{t}</span>)}
          </div>

          <h1 className="project-title">{project.title}</h1>

          <hr className="section-divider" />

          {/* Case study sections */}
          {CASE_SECTIONS.map(({ key, label }) => {
            const value = project[key] as any[]
            if (!value?.length) return null
            return (
              <div key={key} className="case-section">
                <div className="case-section-head">{label}</div>
                <div className="case-section-body">
                  <PortableText value={value} components={ptComponents} />
                </div>
              </div>
            )
          })}

          {/* Gallery */}
          {project.gallery && project.gallery.length > 0 && (
            <div className="case-section">
              <div className="case-section-head">Gallery</div>
              <div className="gallery-scroll">
                {project.gallery.map((img: SanityImage, i: number) => (
                  <div key={i} style={{ flexShrink: 0 }}>
                    <Image
                      src={urlFor(img).width(1200).height(675).url()}
                      alt={img.alt ?? `Gallery image ${i + 1}`}
                      width={1200}
                      height={675}
                      className="gallery-img"
                    />
                    {img.caption && (
                      <div className="gallery-caption">{img.caption}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Project link */}
          {project.projectUrl && (
            <div style={{ marginBottom: 52 }}>
              <a href={project.projectUrl} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                View Project ↗
              </a>
            </div>
          )}

          <Link href="/projects" className="btn">← Back to All Projects</Link>
        </div>
      </main>

      <footer className="footer">
        <div className="container">Built from scratch · Hosted on Vercel</div>
      </footer>
    </>
  )
}
