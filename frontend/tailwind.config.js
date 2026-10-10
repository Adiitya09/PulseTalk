import tailwindForms from '@tailwindcss/forms'
import tailwindTypography from '@tailwindcss/typography'

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
        // Google-inspired color palette
        google: {
          blue: {
            50: '#e8f0fe',
            100: '#d2e3fc',
            200: '#aecbfa',
            300: '#8ab4f8',
            400: '#669df6',
            500: '#4285f4', // Primary Google Blue
            600: '#1a73e8',
            700: '#1967d2',
            800: '#185abc',
            900: '#174ea6',
          },
          red: {
            50: '#fce8e6',
            100: '#fad2cf',
            200: '#f6aea9',
            300: '#f28b82',
            400: '#ee675c',
            500: '#ea4335', // Google Red
            600: '#d93025',
            700: '#c5221f',
            800: '#b31412',
            900: '#a50e0e',
          },
          yellow: {
            50: '#fef7e0',
            100: '#feefc3',
            200: '#fde293',
            300: '#fdd663',
            400: '#fcc934',
            500: '#fbbc04', // Google Yellow
            600: '#f9ab00',
            700: '#f29900',
            800: '#ea8600',
            900: '#e37400',
          },
          green: {
            50: '#e6f4ea',
            100: '#ceead6',
            200: '#a8dab5',
            300: '#81c995',
            400: '#5bb974',
            500: '#34a853', // Google Green
            600: '#1e8e3e',
            700: '#188038',
            800: '#137333',
            900: '#0d652d',
          },
        },
        // Sentiment colors
        sentiment: {
          positive: '#34a853',
          negative: '#ea4335',
          neutral: '#5f6368'
        },
        // Dark mode colors
        dark: {
          bg: {
            primary: '#0a0a0a',
            secondary: '#1a1a1a',
            tertiary: '#2a2a2a',
          },
          text: {
            primary: '#e8eaed',
            secondary: '#9aa0a6',
            tertiary: '#5f6368',
          },
          border: '#3c4043',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Poppins', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      fontSize: {
        'display-xl': ['4.5rem', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        'display-lg': ['3.75rem', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        'display-md': ['3rem', { lineHeight: '1.2', letterSpacing: '-0.01em' }],
        'display-sm': ['2.25rem', { lineHeight: '1.3', letterSpacing: '-0.01em' }],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-down': 'slideDown 0.5s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
        'bounce-slow': 'bounce 3s infinite',
        'gradient': 'gradient 8s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.9)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        gradient: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-google': 'linear-gradient(135deg, #4285f4 0%, #ea4335 25%, #fbbc04 50%, #34a853 75%, #4285f4 100%)',
        'gradient-blue': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'gradient-green': 'linear-gradient(135deg, #34a853 0%, #1e8e3e 100%)',
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
        'glass-lg': '0 12px 48px 0 rgba(31, 38, 135, 0.2)',
        'glow-blue': '0 0 20px rgba(66, 133, 244, 0.3)',
        'glow-green': '0 0 20px rgba(52, 168, 83, 0.3)',
        'glow-red': '0 0 20px rgba(234, 67, 53, 0.3)',
      },
    },
  },
  plugins: [
    tailwindForms,
    tailwindTypography,
  ],
}
