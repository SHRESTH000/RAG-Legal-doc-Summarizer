import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          primary: '#0d0d0d',
          secondary: '#171717',
          tertiary: '#262626',
        },
        border: {
          default: '#2d2d2d',
          muted: '#404040',
        },
        text: {
          primary: '#ececec',
          secondary: '#a1a1a1',
          muted: '#737373',
        },
      },
    },
  },
  plugins: [],
};

export default config;
