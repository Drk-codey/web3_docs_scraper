/** @type {import('tailwindcss').Config} */

module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: { 
    extend: {
      colors: {
        // primary: '#4F46E5',
        // secondary: '#6D28D9',
        // accent: '#8B5CF6',
        // background: '#1F2937',
        // foreground: '#F3F4F6',
      }
    } 
  },
  plugins: [],
};
