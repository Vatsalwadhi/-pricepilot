export type Platform = {
  id: number;
  name: string;
  slug: string;
  provider_key: string;
  is_active: boolean;
  logo_url?: string;
  brand_color?: string;
};

export type Product = {
  id: number;
  display_name: string;
  normalized_name: string;
  quantity: string;
  brand: string;
};

export type ComparisonResult = {
  id: number;
  platform: Platform | null;
  product: Product | null;
  product_name: string;
  normalized_product_name: string;
  quantity: string;
  currency: string;
  price: string | null;
  delivery_charge: string | null;
  total_price: string | null;
  product_url: string;
  is_cheapest: boolean;
  error_message: string;
  price_difference_from_cheapest: string | null;
  image: string | null;
  mrp: number | null;
  brand: string | null;
  raw_payload?: {
    eta?: string;
    delivery_time?: string;
    image?: string;
    image_url?: string;
    mrp?: string | number;
  };
  created_at: string;
};

export type SearchHistoryItem = {
  id: number;
  query: string;
  normalized_query: string;
  cheapest_platform: Platform | null;
  cheapest_total_price: string | null;
  highest_total_price: string | null;
  savings: string | null;
  result_count?: number;
  created_at: string;
};

export type ProductDiscovery = {
  id: string;
  normalized_id: string;
  brand: string;
  display_name: string;
  quantity: string;
  variant: string;
  image: string;
  category: string;
  available_platforms: {
    name: string;
    logo_url?: string;
    brand_color?: string;
    provider_key: string;
  }[];
  lowest_price: string;
  highest_price: string;
  offers_count: number;
};

export type Comparison = SearchHistoryItem & {
  results: ProductDiscovery[];
};

export type ProductOffersResponse = {
  product: {
    name: string;
    brand: string;
    quantity: string;
    image: string;
  };
  analytics: {
    lowest_product_price: number;
    lowest_total_cost: number;
    highest_price: number;
    average_price: number;
    money_saved: number;
    cheapest_provider: string;
    platforms_compared: number;
    fastest_delivery: string | null;
    highest_discount: number;
  };
  platforms: {
    platform: {
      id: number;
      name: string;
      logo_url?: string;
      brand_color?: string;
    };
    status: 'available' | 'not_available' | 'not_serviceable' | 'error' | 'coming_soon';
    status_message: string;
    offer: ComparisonResult | null;
  }[];
  similar_alternatives?: {
    product: {
      normalized_id: string;
      name: string;
      brand: string;
      quantity: string;
      price: string;
      image: string;
    };
    evaluation: {
      comparable: boolean;
      score: number;
      reason: string;
      same_brand: boolean;
      same_variant: boolean;
      same_quantity: boolean;
      same_category: boolean;
      preferred_match: boolean;
    };
  }[];
};
