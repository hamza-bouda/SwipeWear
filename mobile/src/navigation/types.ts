import type { Product } from '../types';

export type RootStackParamList = {
  GenderLanguage: undefined;
  Onboarding: undefined;
  StyleSelection: undefined;
  ImageImport: undefined;
  Constraints: { route: 'styles' | 'images'; selectedStyles?: string[]; imageUris?: string[] };
  Main: undefined;
  ProductDetail: { productId: string; product?: Product };
  PriceLadder: { productId: string };
  Login: undefined;
  Algorithm: undefined;
};

export type MainTabParamList = {
  Feed: undefined;
  Drop: undefined;
  Alerts: undefined;
  Dressing: undefined;
  Profile: undefined;
};
