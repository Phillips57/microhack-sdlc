import axios from 'axios';
import { api } from './config';

export interface CartItem {
  productId: number;
  name: string;
  imgName: string | null;
  unitPrice: number;
  quantity: number;
  lineTotal: number;
}

export interface Cart {
  cartId: string;
  items: CartItem[];
  itemCount: number;
  total: number;
}

export interface AddCartItemRequest {
  productId: number;
  quantity: number;
}

export interface UpdateCartItemRequest {
  quantity: number;
}

const CART_REQUEST_TIMEOUT_MS = 10_000;

interface ApiError {
  error?: {
    message?: string;
  };
}

const CART_ID_STORAGE_KEY = 'octocat-cart-id';

export function getCartId(): string {
  const savedCartId = localStorage.getItem(CART_ID_STORAGE_KEY);
  if (savedCartId) {
    return savedCartId;
  }

  const cartId = crypto.randomUUID();
  localStorage.setItem(CART_ID_STORAGE_KEY, cartId);
  return cartId;
}

export function getCartErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiError>(error)) {
    return error.response?.data?.error?.message ?? error.message;
  }
  return error instanceof Error ? error.message : 'Unable to update your cart.';
}

export async function fetchCart(cartId: string): Promise<Cart> {
  const { data } = await axios.get<Cart>(
    `${api.baseURL}${api.endpoints.cart}/${encodeURIComponent(cartId)}`,
    { timeout: CART_REQUEST_TIMEOUT_MS },
  );
  return data;
}

export async function addCartItem(
  cartId: string,
  request: AddCartItemRequest,
): Promise<Cart> {
  const { data } = await axios.post<Cart>(
    `${api.baseURL}${api.endpoints.cart}/${encodeURIComponent(cartId)}/items`,
    request,
  );
  return data;
}

export async function updateCartItem(
  cartId: string,
  productId: number,
  request: UpdateCartItemRequest,
): Promise<Cart> {
  const { data } = await axios.put<Cart>(
    `${api.baseURL}${api.endpoints.cart}/${encodeURIComponent(cartId)}/items/${productId}`,
    request,
  );
  return data;
}

export async function removeCartItem(cartId: string, productId: number): Promise<void> {
  await axios.delete(
    `${api.baseURL}${api.endpoints.cart}/${encodeURIComponent(cartId)}/items/${productId}`,
  );
}
