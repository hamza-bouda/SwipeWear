export const colors = {
  primary: '#000000',
  secondary: '#FFFFFF',
  accent: '#FACC15',
  accentDark: '#EAB308',
  accentLight: '#FEF9C3',
  accentText: '#000000',
  background: '#FFFFFF',
  surface: '#FAFAFA',
  textPrimary: '#0A0A0A',
  textSecondary: '#666666',
  textInverse: '#FFFFFF',
  border: '#E5E5E5',
  disabled: '#CCCCCC',
  success: '#34C759',
  warning: '#FF9500',
  error: '#FF3B30',
  overlay: 'rgba(0, 0, 0, 0.5)',
} as const;

export type ColorKey = keyof typeof colors;
