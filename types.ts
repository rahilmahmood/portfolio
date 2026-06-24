export interface SanityImage {
  _type: 'image'
  asset: { _ref: string; _type: 'reference' }
  hotspot?: { x: number; y: number }
  alt?: string
  caption?: string
}

export interface Project {
  _id: string
  title: string
  slug: { current: string }
  date: string
  category: string
  summary: string
  heroImage?: SanityImage
  tools: string[]
  featured: boolean
  overview?: any[]
  problemGoal?: any[]
  whatIBuilt?: any[]
  engineeringDecisions?: any[]
  results?: any[]
  gallery?: SanityImage[]
  nextSteps?: any[]
  projectUrl?: string
}

export interface ProjectStub {
  _id: string
  title: string
  slug: { current: string }
  date: string
  category: string
  summary: string
  heroImage?: SanityImage
  tools: string[]
  featured: boolean
}
