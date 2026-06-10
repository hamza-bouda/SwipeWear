export type RootStackParamList = {
  Onboarding: undefined;
  StyleSelection: undefined;
  ImageImport: undefined;
  Constraints: { route: 'styles' | 'images'; selectedStyles?: string[]; imageUris?: string[] };
  Main: undefined;
  ProductDetail: { productId: string };
};

export type MainTabParamList = {
  Feed: undefined;
  Saves: undefined;
  Profile: undefined;
};
