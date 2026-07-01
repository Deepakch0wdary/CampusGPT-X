/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#0070f3',
          600: '#0060d9',
          900: '#0c2340',
        }
      }
    },
  },
  plugins: [],
  corePlugins: {
    // Avoid conflicting with MUI baseline css resets
    preflight: true,
  }
}
