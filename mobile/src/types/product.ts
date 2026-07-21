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
  recommendationReason?: string;
}
