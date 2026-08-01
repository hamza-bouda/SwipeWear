export interface Product {
  id: string;
  title: string;
  brand: string;
  price: number;
  currency: string;
  condition: string;
  category: string;
  size: string | null;
  imageUrls: string[];
  source: string;
  available?: boolean;
  /** Seller listing URL served by the API, affiliate-wrapped when enabled. */
  url?: string;
  recommendationReason?: string;
}
