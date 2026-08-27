import colors from 'tailwindcss/colors';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // StoryForge AI Core Palette
        brand: {
          400: '#7357FF', // Violet
          500: '#5B37FF',
          600: '#4318FF', // Deep Indigo (Primary Brand)
          700: '#3311CC',
          DEFAULT: '#4318FF',
        },
        accent: {
          orange: '#FF5523', // Accent Orange / CTA
          500: '#FF5523',
          DEFAULT: '#FF5523',
        },
        dark: {
          700: '#2B3674', // Slate Grey / Sub Headings
          900: '#11142D', // Main Slate
          950: '#1B1E3A', // Sidebar BG
          sub: '#111827',
        },
        neutral: {
          card: '#FFFFFF',
          bg: '#F4F7FE',
          muted: '#F4F7FE',
          border: '#E0E5F2',
          subtext: '#A3AED0',
          medium: '#707EAE',
          text: '#1B2559',
        },
        success: {
          50: '#E6F9F0',
          500: '#05CD99', // Emerald
          600: '#02C069', // Bright Green
          DEFAULT: '#05CD99',
        },
        warning: {
          500: '#FFB800', // Amber
          DEFAULT: '#FFB800',
        },
        info: {
          50: '#EAEFFF',
          100: '#D6E4FF',
          500: '#3965FF', // Royal Blue
          DEFAULT: '#3965FF',
        },
        error: {
          50: '#FDEDEC',
          500: '#EE5D50',
          DEFAULT: '#EE5D50',
        },
        // Mapping standard tailwind color slots to match StoryForge colors
        sky: {
          50: '#F4F7FE',
          100: '#EAEFFF',
          200: '#D6E4FF',
          300: '#7357FF',
          400: '#7357FF',
          500: '#4318FF',
          600: '#3311CC',
          700: '#280CA0',
          800: '#1E0775',
          900: '#1B1E3A',
          950: '#11142D',
        },
        blue: {
          50: '#EAEFFF',
          100: '#D6E4FF',
          200: '#B8CFFF',
          300: '#7357FF',
          400: '#3965FF',
          500: '#4318FF',
          600: '#3311CC',
          700: '#2B3674',
          800: '#1B1E3A',
          900: '#11142D',
          950: '#0B0E23',
        },
        slate: {
          50: '#F4F7FE',   // Workspace BG
          100: '#E0E5F2',  // Standard Border
          200: '#E0E5F2',  // Standard Border
          300: '#CBD5E1',
          400: '#A3AED0',  // Light Muted Text
          500: '#707EAE',  // Subtext Medium
          600: '#2B3674',  // Dark Slate Grey
          700: '#1B2559',  // Pure Dark Text
          800: '#1B1E3A',  // Dark Sidebar / Card
          900: '#11142D',  // Main Slate
          950: '#0B0E23',
        },
      },
      animation: {
        'stripe': 'stripe 2s linear infinite',
        'pulse-subtle': 'pulseSubtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'seg-fill': 'segFill 2.8s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards',
        'seg-shimmer': 'segShimmer 1.8s ease-in-out infinite',
        'seg-pulse': 'segPulse 2s ease-in-out infinite',
      },
      keyframes: {
        stripe: {
          '0%': { backgroundPosition: '1rem 0' },
          '100%': { backgroundPosition: '0 0' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.7 },
        },
        segFill: {
          '0%': { transform: 'scaleX(0)' },
          '100%': { transform: 'scaleX(1)' },
        },
        segShimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(200%)' },
        },
        segPulse: {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.65 },
        },
      }
    },
  },
  plugins: [],
}

