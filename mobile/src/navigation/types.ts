export type RootStackParamList = {
  Onboarding: undefined;
  StyleSelection: undefined;
  ImageImport: undefined;
  Constraints: { route: 'styles' | 'images'; selectedStyles?: string[]; imageUris?: string[] };
  Main: undefined;
  ProductDetail: { productId: string };
  PriceLadder: { productId: string };
  Login: undefined;
  Algorithm: undefined;
};

export type MainTabParamList = {
  Feed: undefined;
  Saves: undefined;
  Profile: undefined;
};
