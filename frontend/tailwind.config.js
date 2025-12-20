/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['DM Sans', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        bg: '#f8f9fb',
        surface: {
          DEFAULT: '#ffffff',
          elevated: '#ffffff',
        },
        sidebar: {
          DEFAULT: '#1a1d21',
          hover: '#2d3139',
          active: '#3b82f6',
        },
        text: {
          DEFAULT: '#111827',
          secondary: '#6b7280',
          muted: '#9ca3af',
          inverse: '#f9fafb',
        },
        primary: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
          light: '#eff6ff',
        },
        success: {
          DEFAULT: '#10b981',
          light: '#d1fae5',
        },
        warning: {
          DEFAULT: '#f59e0b',
          light: '#fef3c7',
        },
        danger: {
          DEFAULT: '#ef4444',
          light: '#fee2e2',
        },
        border: {
          DEFAULT: '#e5e7eb',
          light: '#f3f4f6',
        },
      },
      borderRadius: {
        sm: '6px',
        md: '8px',
        lg: '12px',
        xl: '16px',
      },
      boxShadow: {
        sm: '0 1px 2px rgba(0, 0, 0, 0.04)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -1px rgba(0, 0, 0, 0.04)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)',
      },
      spacing: {
        'sidebar': '240px',
        'sidebar-collapsed': '72px',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease',
        'slide-down': 'slideDown 0.3s ease',
        'slide-in': 'slideIn 0.3s ease backwards',
        'modal-slide': 'modalSlide 0.3s ease',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          from: { opacity: '0', transform: 'translateY(-10px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          from: { opacity: '0', transform: 'translateX(-12px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        modalSlide: {
          from: { opacity: '0', transform: 'translateY(20px) scale(0.98)' },
          to: { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
}
