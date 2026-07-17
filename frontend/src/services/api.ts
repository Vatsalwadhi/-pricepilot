import type { Comparison, SearchHistoryItem, ProductOffersResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    },
    ...init
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch {
      // Keep the HTTP status message when the response is not JSON.
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function searchProducts(query: string, lat?: number | null, lon?: number | null): Promise<Comparison> {
  const payload: any = { query };
  if (lat != null && lon != null) {
    payload.lat = lat;
    payload.lon = lon;
  }
  return request<Comparison>("/search", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function deepSearchProduct(query: string, lat?: number | null, lon?: number | null): Promise<Comparison> {
  const payload: any = { query };
  if (lat != null && lon != null) {
    payload.lat = lat;
    payload.lon = lon;
  }
  return request<Comparison>("/comparison/deep", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getProductHistory(normalizedName: string): Promise<any[]> {
  return request<any[]>(`/products/${encodeURIComponent(normalizedName)}/history`);
}

export function getProductOffers(normalizedName: string, searchId?: string): Promise<ProductOffersResponse> {
  let url = `/products/${encodeURIComponent(normalizedName)}/offers`;
  if (searchId) {
    url += `?search_id=${encodeURIComponent(searchId)}`;
  }
  return request<ProductOffersResponse>(url);
}

export function getHistory(): Promise<SearchHistoryItem[]> {
  return request<SearchHistoryItem[]>("/history");
}

export function getComparison(id: string | number): Promise<Comparison> {
  return request<Comparison>(`/comparison/${id}`);
}

export function deleteHistoryItem(id: string | number): Promise<void> {
  return request<void>(`/history/${id}`, { method: "DELETE" });
}

export function createPriceAlert(productName: string, normalizedProductName: string, targetPrice: number): Promise<{detail: string, id: number}> {
  return request<{detail: string, id: number}>("/alerts/", {
    method: "POST",
    body: JSON.stringify({
      product_name: productName,
      normalized_product_name: normalizedProductName,
      target_price: targetPrice
    })
  });
}
