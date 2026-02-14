import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'ignition-lint',
  tagline: 'Lint your Ignition projects like a pro',
  favicon: 'img/favicon.ico',

  future: {
    v4: true,
  },

  url: 'https://TheThoughtagen.github.io',
  baseUrl: '/ignition-lint/',

  organizationName: 'TheThoughtagen',
  projectName: 'ignition-lint',

  onBrokenLinks: 'warn',

  markdown: {
    format: 'md',
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          path: '../docs',
          sidebarPath: './sidebars.ts',
          editUrl:
            'https://github.com/TheThoughtagen/ignition-lint/tree/main/docs/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    colorMode: {
      defaultMode: 'dark',
      disableSwitch: false,
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: 'ignition-lint',
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          href: 'https://github.com/TheThoughtagen/ignition-lint',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentation',
          items: [
            {label: 'Getting Started', to: '/docs/getting-started/installation'},
            {label: 'CLI Reference', to: '/docs/guides/cli-reference'},
            {label: 'Suppression', to: '/docs/guides/suppression'},
          ],
        },
        {
          title: 'Integration',
          items: [
            {label: 'GitHub Actions', to: '/docs/integration/github-actions'},
            {label: 'Pre-commit', to: '/docs/integration/pre-commit'},
            {label: 'MCP Server', to: '/docs/guides/mcp-server'},
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/TheThoughtagen/ignition-lint',
            },
            {
              label: 'Credits',
              to: '/docs/credits',
            },
          ],
        },
      ],
      copyright: `Copyright &copy; ${new Date().getFullYear()} Whiskey House Labs. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'json', 'yaml', 'python'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
