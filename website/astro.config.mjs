import { defineConfig } from 'astro/config'
import starlight from '@astrojs/starlight'
import starlightThemeFlexoki from 'starlight-theme-flexoki'
import { createHash } from 'node:crypto'
import { readFileSync, writeFileSync, readdirSync, statSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'

function allHtmlFiles(dir) {
  const results = []
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    if (statSync(full).isDirectory()) {
      results.push(...allHtmlFiles(full))
    } else if (entry.endsWith('.html')) {
      results.push(full)
    }
  }
  return results
}

function injectCsp() {
  return {
    name: 'inject-csp',
    hooks: {
      'astro:build:done': async ({ dir }) => {
        const distDir = fileURLToPath(dir)
        const files = allHtmlFiles(distDir)
        for (const file of files) {
          let html = readFileSync(file, 'utf-8')
          const hashes = new Set()
          const pattern = /<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g
          for (const match of html.matchAll(pattern)) {
            const src = match[1]
            if (!src.trim()) continue
            hashes.add(`'sha256-${createHash('sha256').update(src).digest('base64')}'`)
          }
          const scriptSrc = ["'self'", ...hashes].join(' ')
          const csp = [
            `default-src 'self'`,
            `script-src ${scriptSrc}`,
            `style-src 'self' 'unsafe-inline' https://fonts.googleapis.com`,
            `font-src 'self' https://fonts.gstatic.com`,
            `img-src 'self' data:`,
            `connect-src 'self'`,
          ].join('; ')
          writeFileSync(
            file,
            html.replace('<head>', `<head><meta http-equiv="Content-Security-Policy" content="${csp}">`),
            'utf-8'
          )
        }
        console.log(`  [inject-csp] Injected CSP into ${files.length} HTML files`)
      },
    },
  }
}

export default defineConfig({
  site: 'https://moat-spec.org',
  base: process.env.ASTRO_BASE_PATH || '/',
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
    injectCsp(),
  ],
})
