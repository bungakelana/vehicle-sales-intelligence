/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,ts}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)', surface: 'var(--surface)', border: 'var(--border)', text: 'var(--text)',
        muted: 'var(--muted)', primary: 'var(--primary)', accent: 'var(--accent)',
        highlight: 'var(--highlight)', positive: 'var(--positive)', negative: 'var(--negative)',
      },
      borderRadius: { card: '12px' },
      fontFamily: { sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'] },
    },
  },
};
