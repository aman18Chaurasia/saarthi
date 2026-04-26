/**
 * SAARTHI Design System
 *
 * Modern, professional design tokens for AI voice agent platform
 */

export const designSystem = {
  colors: {
    // Brand colors - Professional blue gradient
    brand: {
      primary: '#3B82F6',      // Blue-500
      secondary: '#8B5CF6',    // Violet-500
      accent: '#10B981',       // Emerald-500
      dark: '#1E293B',         // Slate-800
      light: '#F1F5F9',        // Slate-100
    },

    // Semantic colors
    success: '#10B981',        // Emerald-500
    warning: '#F59E0B',        // Amber-500
    error: '#EF4444',          // Red-500
    info: '#3B82F6',           // Blue-500

    // Neutral palette
    neutral: {
      50: '#F8FAFC',
      100: '#F1F5F9',
      200: '#E2E8F0',
      300: '#CBD5E1',
      400: '#94A3B8',
      500: '#64748B',
      600: '#475569',
      700: '#334155',
      800: '#1E293B',
      900: '#0F172A',
    },

    // Glass effects
    glass: {
      light: 'rgba(255, 255, 255, 0.1)',
      medium: 'rgba(255, 255, 255, 0.15)',
      dark: 'rgba(0, 0, 0, 0.2)',
    },
  },

  typography: {
    fontFamily: {
      sans: 'Inter, system-ui, sans-serif',
      mono: 'JetBrains Mono, monospace',
    },

    fontSize: {
      xs: '0.75rem',      // 12px
      sm: '0.875rem',     // 14px
      base: '1rem',       // 16px
      lg: '1.125rem',     // 18px
      xl: '1.25rem',      // 20px
      '2xl': '1.5rem',    // 24px
      '3xl': '1.875rem',  // 30px
      '4xl': '2.25rem',   // 36px
      '5xl': '3rem',      // 48px
    },

    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },

    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.75,
    },
  },

  spacing: {
    0: '0',
    1: '0.25rem',    // 4px
    2: '0.5rem',     // 8px
    3: '0.75rem',    // 12px
    4: '1rem',       // 16px
    5: '1.25rem',    // 20px
    6: '1.5rem',     // 24px
    8: '2rem',       // 32px
    10: '2.5rem',    // 40px
    12: '3rem',      // 48px
    16: '4rem',      // 64px
    20: '5rem',      // 80px
    24: '6rem',      // 96px
  },

  borderRadius: {
    none: '0',
    sm: '0.25rem',    // 4px
    md: '0.5rem',     // 8px
    lg: '0.75rem',    // 12px
    xl: '1rem',       // 16px
    '2xl': '1.5rem',  // 24px
    full: '9999px',
  },

  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    glow: '0 0 20px rgba(59, 130, 246, 0.5)',
    glowGreen: '0 0 20px rgba(16, 185, 129, 0.5)',
    glowPurple: '0 0 20px rgba(139, 92, 246, 0.5)',
  },

  transitions: {
    fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
    base: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
    slow: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: '500ms cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  },

  zIndex: {
    base: 0,
    dropdown: 10,
    sticky: 20,
    modal: 30,
    popover: 40,
    toast: 50,
  },
} as const;

// Animation presets
export const animations = {
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },

  slideUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  },

  slideRight: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 20 },
  },

  scale: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 },
  },

  bounce: {
    initial: { opacity: 0, scale: 0.3 },
    animate: {
      opacity: 1,
      scale: 1,
      transition: { type: 'spring', stiffness: 200, damping: 10 }
    },
    exit: { opacity: 0, scale: 0.3 },
  },
};

// Component variants
export const variants = {
  button: {
    primary: 'bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white shadow-lg hover:shadow-glow',
    secondary: 'bg-white/10 hover:bg-white/20 text-white border border-white/20 backdrop-blur-sm',
    success: 'bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 text-white shadow-lg hover:shadow-glowGreen',
    danger: 'bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-500 hover:to-pink-500 text-white shadow-lg',
    ghost: 'bg-transparent hover:bg-white/10 text-white',
  },

  card: {
    glass: 'bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl shadow-xl',
    solid: 'bg-slate-800 border border-slate-700 rounded-2xl shadow-xl',
    glow: 'bg-gradient-to-br from-blue-500/10 to-violet-500/10 backdrop-blur-md border border-blue-500/20 rounded-2xl shadow-glow',
  },

  badge: {
    success: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
    warning: 'bg-amber-500/20 text-amber-400 border border-amber-500/30',
    error: 'bg-red-500/20 text-red-400 border border-red-500/30',
    info: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
    neutral: 'bg-slate-500/20 text-slate-400 border border-slate-500/30',
  },
};

// Glassmorphism utilities
export const glass = {
  light: 'bg-white/10 backdrop-blur-lg border border-white/20',
  medium: 'bg-white/15 backdrop-blur-xl border border-white/30',
  dark: 'bg-black/20 backdrop-blur-lg border border-white/10',
};

// Gradient backgrounds
export const gradients = {
  primary: 'bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800',
  blue: 'bg-gradient-to-br from-blue-950 via-blue-900 to-slate-900',
  purple: 'bg-gradient-to-br from-violet-950 via-purple-900 to-slate-900',
  mesh: 'bg-gradient-to-br from-slate-950 via-blue-950 to-violet-950',
};
