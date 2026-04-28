import { defineConfig } from 'astro/config'
import starlight from '@astrojs/starlight'
import starlightThemeFlexoki from 'starlight-theme-flexoki'

export default defineConfig({
  site: 'https://moat-spec.org',
  integrations: [
    starlight({
      title: 'MOAT',
      description:
        'Model for Origin Attestation and Trust — an open protocol for provenance and integrity of AI agent content.',
      plugins: [starlightThemeFlexoki()],
      customCss: ['./src/styles/custom.css'],
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/OpenScribbler/moat',
        },
      ],
      sidebar: [
        {
          label: 'Overview',
          items: [
            { label: 'What is MOAT?', slug: 'overview/what-is-moat' },
            { label: 'How it works', slug: 'overview/how-it-works' },
            { label: 'Use cases', slug: 'overview/use-cases' },
            { label: 'Spec status', slug: 'overview/spec-status' },
          ],
        },
        {
          label: 'Specification',
          items: [
            { label: 'Core spec', slug: 'spec/core' },
            { label: 'moat-verify', slug: 'spec/moat-verify' },
            { label: 'Publisher Action', slug: 'spec/publisher-action' },
            { label: 'Registry Action', slug: 'spec/registry-action' },
          ],
        },
        {
          label: 'Guides',
          items: [
            { label: 'For publishers', slug: 'guides/publishers' },
            { label: 'For registry operators', slug: 'guides/registry-operators' },
            { label: 'Self-publishing (both actions)', slug: 'guides/self-publishing' },
            { label: 'For consumers', slug: 'guides/consumers' },
          ],
        },
      ],
    }),
  ],
})
