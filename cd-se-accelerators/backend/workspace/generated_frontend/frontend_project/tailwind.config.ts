import type { Config } from 'tailwindcss';
export default {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
  "primary": "#3498db",
  "secondary": "#f1c40f",
  "background": "#ffffff",
  "text": "#333333"
}
    }
  }
} satisfies Config;