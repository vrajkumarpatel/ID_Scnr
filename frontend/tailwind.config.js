/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        slateglass: {
          800: '#0f172a',
          700: '#1e293b',
          600: '#334155',
        },
        amberglass: {
          500: '#f59e0b',
        }
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [require('@tailwindcss/forms')],
}