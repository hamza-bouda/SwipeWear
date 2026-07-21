export const colors = {
  primary: '#000000',
  secondary: '#FFFFFF',
  accent: '#FF3B30',
  background: '#FFFFFF',
  surface: '#F5F5F5',
  textPrimary: '#000000',
  textSecondary: '#666666',
  textInverse: '#FFFFFF',
  border: '#E0E0E0',
  disabled: '#CCCCCC',
  success: '#34C759',
  warning: '#FF9500',
  error: '#FF3B30',
  overlay: 'rgba(0, 0, 0, 0.5)',
} as const;

export type ColorKey = keyof typeof colors;
