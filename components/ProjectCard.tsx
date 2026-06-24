import Link from 'next/link'
import Image from 'next/image'
import type { ProjectStub } from '@/types'
import { urlFor } from '@/sanity/lib/image'

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

export default function ProjectCard({ project }: { project: ProjectStub }) {
  return (
    <Link href={`/projects/${project.slug.current}`} className="card">
      {project.heroImage ? (
        <Image
          src={urlFor(project.heroImage).width(800).height(450).url()}
          alt={project.heroImage.alt ?? project.title}
          width={800}
          height={450}
          className="card-img"
        />
      ) : (
        <div className="card-img-placeholder">
          <span className="label" style={{ opacity: 0.35 }}>no image yet</span>
        </div>
      )}
      <div className="card-body">
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="tag tag-accent">{project.category}</span>
          {project.date && <span className="label">{formatDate(project.date)}</span>}
        </div>
        <div className="card-title">{project.title}</div>
        <div className="card-desc">{project.summary}</div>
        <div className="card-tags">
          {project.tools?.slice(0, 3).map((t) => (
            <span key={t} className="tag">{t}</span>
          ))}
          {(project.tools?.length ?? 0) > 3 && (
            <span className="tag">+{project.tools.length - 3}</span>
          )}
        </div>
      </div>
    </Link>
  )
}
