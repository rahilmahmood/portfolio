import Nav from '@/components/Nav'

// ── Edit everything in this file to match your real info ─────

export const metadata = {
  title: 'About — Rahil Mahmood',
}

const BIO = [
  "I'm a mechanical engineering student at UT Austin building hardware across vehicles, robotics, and embedded systems — from welded steel FSAE chassis work to autonomous camera prototypes and electronics packaging.",
  "My work sits at the intersection of mechanical design, validation, and hands-on prototyping. A typical week might involve running ANSYS on suspension hardpoints, correlating chassis torsional rigidity data, packaging vehicle electronics, or debugging a Raspberry Pi vision system.",
  "I'm currently the Frame Lead for Longhorn Racing Electric, where I work on FSAE EV chassis design, structural validation, fabrication planning, and cross-team vehicle integration. I'm also doing robotics strategy research at Seanergy.AI, focused on warehouse automation, AMRs, robotics middleware, and vendor evaluation.",
]

const SKILLS = [
  {
    group: 'Mechanical Design',
    items: ['SOLIDWORKS', 'GD&T', 'DFM', 'Weldment Design', 'Electronics Packaging', 'Fixture Design'],
  },
  {
    group: 'Analysis',
    items: ['ANSYS Mechanical', 'FEA', 'Structural Analysis', 'Torsional Rigidity', 'Design Validation', 'Hand Calculations'],
  },
  {
    group: 'Robotics & Programming',
    items: ['Python', 'YOLO', 'OpenCV', 'Raspberry Pi', 'Arduino', 'Computer Vision', 'Motor Control', 'Remote Streaming'],
  },
  {
    group: 'Manufacturing & Prototyping',
    items: ['3D Printing', 'Welding', 'Shop Drawings', 'Heat-Set Inserts', 'O-Ring Design', 'ESC Calibration', 'Bench Testing'],
  },
]

const RESUME_URL = '/resume.pdf'
const LINKEDIN_URL = 'https://www.linkedin.com/in/rahilmahmood/'

export default function AboutPage() {
  return (
    <>
      <Nav />
      <main className="page">
        <div className="container" style={{ paddingTop: 72 }}>
          <p className="label" style={{ marginBottom: 12 }}>About</p>
          <h1 style={{ fontSize: 'clamp(32px, 5vw, 52px)', marginBottom: 64 }}>The long version.</h1>

          <div className="about-grid">
            {/* Bio */}
            <div>
              {BIO.map((para, i) => (
                <p
                  key={i}
                  style={{
                    fontSize: i === 0 ? 17 : 15,
                    lineHeight: 1.8,
                    color: i === 0 ? 'var(--text)' : 'var(--muted)',
                    marginBottom: 20,
                  }}
                >
                  {para}
                </p>
              ))}

              <div style={{ display: 'flex', gap: 12, marginTop: 36 }}>
                <a href={RESUME_URL} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                  Resume ↗
                </a>
                <a href={LINKEDIN_URL} target="_blank" rel="noopener noreferrer" className="btn">
                  LinkedIn ↗
                </a>
              </div>
            </div>

            {/* Skills */}
            <div>
              <p className="label" style={{ marginBottom: 28 }}>Skills</p>
              {SKILLS.map(({ group, items }) => (
                <div key={group} className="skill-group">
                  <div className="skill-group-label">{group}</div>
                  <div className="skill-row">
                    {items.map((s) => (
                      <span key={s} className="skill-pill">{s}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      <footer className="footer">
        <div className="container">Built from scratch · Hosted on Vercel</div>
      </footer>
    </>
  )
}
