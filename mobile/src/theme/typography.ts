import { TextStyle } from 'react-native';

export const typography: Record<string, TextStyle> = {
  h1: { fontSize: 30, fontWeight: '800', lineHeight: 36, letterSpacing: -0.7 },
  h2: { fontSize: 23, fontWeight: '700', lineHeight: 29, letterSpacing: -0.35 },
  h3: { fontSize: 18, fontWeight: '700', lineHeight: 24 },
  body: { fontSize: 16, fontWeight: '400', lineHeight: 22 },
  bodyBold: { fontSize: 16, fontWeight: '600', lineHeight: 22 },
  caption: { fontSize: 13, fontWeight: '400', lineHeight: 18 },
  captionBold: { fontSize: 13, fontWeight: '600', lineHeight: 18 },
  label: { fontSize: 11, fontWeight: '600', lineHeight: 14, textTransform: 'uppercase', letterSpacing: 0.5 },
};
