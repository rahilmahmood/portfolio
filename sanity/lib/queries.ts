export const projectsQuery = `
  *[_type == "project"] | order(date desc) {
    _id, title, slug, date, category, summary, heroImage, tools, featured
  }
`

export const featuredProjectsQuery = `
  *[_type == "project" && featured == true] | order(date desc) {
    _id, title, slug, date, category, summary, heroImage, tools, featured
  }
`

export const projectBySlugQuery = `
  *[_type == "project" && slug.current == $slug][0] {
    _id, title, slug, date, category, summary, heroImage, tools,
    overview, problemGoal, whatIBuilt, engineeringDecisions,
    results, gallery, nextSteps, projectUrl
  }
`

export const projectSlugsQuery = `
  *[_type == "project"] { "slug": slug.current }
`
