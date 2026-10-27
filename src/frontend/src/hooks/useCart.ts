import { useMutation, useQuery, useQueryClient } from 'react-query';
import {
  addCartItem,
  AddCartItemRequest,
  Cart,
  fetchCart,
  getCartId,
  removeCartItem,
  updateCartItem,
  UpdateCartItemRequest,
} from '../api/cart';

export default function useCart() {
  const cartId = getCartId();
  const queryKey = ['cart', cartId];
  const queryClient = useQueryClient();
  const cartQuery = useQuery<Cart, Error>(queryKey, () => fetchCart(cartId), {
    retry: false,
  });

  const addItem = useMutation(
    (request: AddCartItemRequest) => addCartItem(cartId, request),
    {
      onSuccess: (cart) => {
        queryClient.setQueryData(queryKey, cart);
      },
    },
  );
  const updateItem = useMutation(
    ({ productId, request }: { productId: number; request: UpdateCartItemRequest }) =>
      updateCartItem(cartId, productId, request),
    {
      onSuccess: (cart) => {
        queryClient.setQueryData(queryKey, cart);
      },
    },
  );
  const removeItem = useMutation((productId: number) => removeCartItem(cartId, productId), {
    onSuccess: () => queryClient.invalidateQueries(queryKey),
  });

  return { ...cartQuery, cartId, addItem, updateItem, removeItem };
}
