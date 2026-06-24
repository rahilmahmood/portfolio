import { defineType, defineField } from 'sanity'

export const projectType = defineType({
  name: 'project',
  title: 'Project',
  type: 'document',
  fields: [
    defineField({ name: 'title', title: 'Title', type: 'string', validation: (r) => r.required() }),
    defineField({ name: 'slug', title: 'Slug', type: 'slug', options: { source: 'title' }, validation: (r) => r.required() }),
    defineField({ name: 'date', title: 'Date', type: 'date', validation: (r) => r.required() }),
    defineField({
      name: 'category',
      title: 'Category',
      type: 'string',
      options: { list: ['Mechanical', 'Electrical', 'Robotics', 'Software', 'Research'] },
      validation: (r) => r.required(),
    }),
    defineField({ name: 'featured', title: 'Featured on Home', type: 'boolean', initialValue: false }),
    defineField({ name: 'summary', title: 'Summary', type: 'text', rows: 3, validation: (r) => r.required().max(200) }),
    defineField({ name: 'tools', title: 'Tools / Stack', type: 'array', of: [{ type: 'string' }] }),
    defineField({ name: 'heroImage', title: 'Hero Image', type: 'image', options: { hotspot: true }, fields: [defineField({ name: 'alt', type: 'string', title: 'Alt text' })] }),
    defineField({ name: 'overview', title: 'Overview', type: 'array', of: [{ type: 'block' }] }),
    defineField({ name: 'problemGoal', title: 'Problem / Goal', type: 'array', of: [{ type: 'block' }] }),
    defineField({ name: 'whatIBuilt', title: 'What I Built', type: 'array', of: [{ type: 'block' }] }),
    defineField({ name: 'engineeringDecisions', title: 'Engineering Decisions', type: 'array', of: [{ type: 'block' }] }),
    defineField({ name: 'results', title: 'Results', type: 'array', of: [{ type: 'block' }] }),
    defineField({
      name: 'gallery',
      title: 'Gallery',
      type: 'array',
      of: [{ type: 'image', options: { hotspot: true }, fields: [defineField({ name: 'alt', type: 'string', title: 'Alt text' }), defineField({ name: 'caption', type: 'string', title: 'Caption' })] }],
    }),
    defineField({ name: 'nextSteps', title: 'Next Steps', type: 'array', of: [{ type: 'block' }] }),
    defineField({ name: 'projectUrl', title: 'Project Link (optional)', type: 'url' }),
  ],
  orderings: [{ title: 'Date, newest', name: 'dateDesc', by: [{ field: 'date', direction: 'desc' }] }],
  preview: {
    select: { title: 'title', subtitle: 'category', media: 'heroImage' },
  },
})
