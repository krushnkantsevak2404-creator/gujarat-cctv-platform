/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        police: {
          900: '#070f1e',
          850: '#0b162c',
          800: '#0f1d3a',
          700: '#162b55',
          600: '#1e3d7a',
          500: '#2a55aa',
          gold: '#e5a93c',
        }
      }
    },
  },
  plugins: [],
}
