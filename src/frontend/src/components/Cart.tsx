import { Link } from 'react-router-dom';
import useCart from '../hooks/useCart';
import { getCartErrorMessage } from '../api/cart';
import { useTheme } from '../context/ThemeContext';

export default function Cart() {
  const { data: cart, isLoading, error, updateItem, removeItem } = useCart();
  const { darkMode } = useTheme();
  const textColor = darkMode ? 'text-light' : 'text-gray-800';

  if (isLoading) {
    return (
      <div className={`min-h-screen pt-24 px-4 ${textColor}`} role="status">
        Loading your cart...
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen pt-24 px-4 text-center" role="alert">
        <p className="text-red-600">{getCartErrorMessage(error)}</p>
      </div>
    );
  }

  if (!cart) {
    return null;
  }

  const mutationError = updateItem.error ?? removeItem.error;

  return (
    <section
      className={`min-h-screen ${darkMode ? 'bg-dark' : 'bg-gray-100'} pt-24 pb-16 px-4`}
    >
      <div className="max-w-5xl mx-auto">
        <h1 className={`text-3xl font-bold mb-8 ${textColor}`}>Your Cart</h1>

        {mutationError != null && (
          <p className="mb-6 text-red-600" role="alert">
            {getCartErrorMessage(mutationError)}
          </p>
        )}

        {cart.items.length === 0 ? (
          <div
            className={`rounded-lg p-8 text-center shadow-sm ${darkMode ? 'bg-gray-800' : 'bg-white'}`}
          >
            <p className={`mb-5 ${textColor}`}>Your cart is empty.</p>
            <Link
              to="/products"
              className="inline-block rounded-lg bg-primary px-5 py-2 text-white hover:bg-accent focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
            >
              Browse products
            </Link>
          </div>
        ) : (
          <div className="grid gap-8 lg:grid-cols-[1fr_18rem]">
            <ul className="space-y-4">
              {cart.items.map((item) => (
                <li
                  key={item.productId}
                  className={`flex flex-col gap-4 rounded-lg p-4 shadow-sm sm:flex-row sm:items-center ${darkMode ? 'bg-gray-800' : 'bg-white'}`}
                >
                  {item.imgName && (
                    <img
                      src={`/${item.imgName}`}
                      alt=""
                      className="h-24 w-24 self-center object-contain sm:self-auto"
                    />
                  )}
                  <div className="flex-grow">
                    <h2 className={`font-semibold ${textColor}`}>{item.name}</h2>
                    <p className="text-sm text-gray-500">${item.unitPrice.toFixed(2)} each</p>
                    <p className={`mt-1 font-medium ${textColor}`}>
                      Line total: ${item.lineTotal.toFixed(2)}
                    </p>
                  </div>
                  <div className="flex items-center justify-between gap-4 sm:flex-col sm:items-end">
                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        onClick={() =>
                          updateItem.mutate({
                            productId: item.productId,
                            request: { quantity: Math.max(1, item.quantity - 1) },
                          })
                        }
                        disabled={updateItem.isLoading || removeItem.isLoading || item.quantity <= 1}
                        aria-label={`Decrease quantity of ${item.name}`}
                        className="h-9 w-9 rounded border border-gray-300 disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-primary"
                      >
                        -
                      </button>
                      <span aria-label={`Quantity of ${item.name}`} className={textColor}>
                        {item.quantity}
                      </span>
                      <button
                        type="button"
                        onClick={() =>
                          updateItem.mutate({
                            productId: item.productId,
                            request: { quantity: item.quantity + 1 },
                          })
                        }
                        disabled={updateItem.isLoading || removeItem.isLoading}
                        aria-label={`Increase quantity of ${item.name}`}
                        className="h-9 w-9 rounded border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
                      >
                        +
                      </button>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeItem.mutate(item.productId)}
                      disabled={updateItem.isLoading || removeItem.isLoading}
                      className="text-sm text-red-600 underline hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
                      aria-label={`Remove ${item.name} from cart`}
                    >
                      Remove
                    </button>
                  </div>
                </li>
              ))}
            </ul>

            <aside
              className={`h-fit rounded-lg p-6 shadow-sm ${darkMode ? 'bg-gray-800' : 'bg-white'}`}
              aria-label="Order summary"
            >
              <h2 className={`text-xl font-semibold ${textColor}`}>Order summary</h2>
              <p className={`mt-3 ${textColor}`}>Items: {cart.itemCount}</p>
              <p className={`mt-2 text-2xl font-bold ${textColor}`}>
                Total: ${cart.total.toFixed(2)}
              </p>
              <p className="mt-3 text-sm text-gray-500">
                Payment is not available yet. Your cart is saved for later.
              </p>
            </aside>
          </div>
        )}
      </div>
    </section>
  );
}
