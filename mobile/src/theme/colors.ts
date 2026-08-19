export const colors = {
  // Core SwipeWear identity: ink, warm white and the signature discovery yellow.
  primary: '#FFD60A',
  secondary: '#F6F5F0',
  accent: '#FFD60A',
  accentDark: '#B98000',
  accentLight: '#FFF5B8',
  accentText: '#0A0A0A',
  background: '#FFFEF9',
  surface: '#F6F5F0',
  surfaceElevated: '#FFFFFF',
  textPrimary: '#171717',
  textSecondary: '#6D6A62',
  textTertiary: '#969187',
  textInverse: '#FFFFFF',
  border: '#E9E6DD',
  borderStrong: '#D4D0C5',
  disabled: '#B9B5AA',
  success: '#16a34a',
  warning: '#f59e0b',
  error: '#dc2626',
  overlay: 'rgba(0, 0, 0, 0.5)',
  gold: '#B98000',
  goldBg: '#FFF8D9',
  cardBg: '#ECE9E0',
} as const;

export type ColorKey = keyof typeof colors;
