// Dev: Vite (5173) and Django (8000) run as separate servers, so point at :8000
// explicitly. Production build: Django serves the built frontend itself (same
// origin, e.g. on PythonAnywhere), so an empty base (relative URLs) is correct.
// VITE_API_URL overrides both when the API lives on a different host/port.
const API_BASE =
  import.meta.env.VITE_API_URL ??
  (import.meta.env.DEV ? `${window.location.protocol}//${window.location.hostname}:8000` : "");

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  return localStorage.getItem("nubeno_token");
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Token ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 204) {
    return undefined as T;
  }

  const isJson = res.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await res.json() : undefined;

  if (!res.ok) {
    const message = data?.detail || data?.non_field_errors?.[0] || res.statusText;
    throw new ApiError(res.status, message);
  }

  return data as T;
}

export const api = {
  login: (username: string, password: string) =>
    apiFetch<{ token: string; username: string; is_admin: boolean; initials: string }>("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: () => apiFetch<void>("/api/auth/logout/", { method: "POST" }),
  getMenu: () => apiFetch<import("./types").Category[]>("/api/menu/"),
  getTables: () => apiFetch<import("./types").Table[]>("/api/tables/"),
  openTableOrder: (tableId: number) =>
    apiFetch<import("./types").Order>(`/api/tables/${tableId}/open-order/`, { method: "POST" }),
  getOrder: (orderId: number) => apiFetch<import("./types").Order>(`/api/orders/${orderId}/`),
  addOrderItem: (
    orderId: number,
    payload: { menu_item_id: number; quantity?: number; note?: string; removed_modifier_option_ids?: number[] }
  ) =>
    apiFetch<import("./types").Order>(`/api/orders/${orderId}/items/`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateOrderItem: (
    orderId: number,
    itemId: number,
    payload: { quantity?: number; note?: string; removed_modifier_option_ids?: number[] }
  ) =>
    apiFetch<import("./types").Order>(`/api/orders/${orderId}/items/${itemId}/`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteOrderItem: (orderId: number, itemId: number) =>
    apiFetch<import("./types").Order>(`/api/orders/${orderId}/items/${itemId}/`, { method: "DELETE" }),
  payOrder: (orderId: number, itemIds: number[] | undefined, paymentMethod: import("./types").PaymentMethod) =>
    apiFetch<import("./types").PayResult>(`/api/orders/${orderId}/pay/`, {
      method: "POST",
      body: JSON.stringify({ item_ids: itemIds ?? [], payment_method: paymentMethod }),
    }),
  cancelOrder: (orderId: number) =>
    apiFetch<import("./types").Order>(`/api/orders/${orderId}/cancel/`, { method: "POST" }),
  transferOrder: (orderId: number, tableId: number) =>
    apiFetch<import("./types").Order>(`/api/orders/${orderId}/transfer/`, {
      method: "POST",
      body: JSON.stringify({ table_id: tableId }),
    }),
  getAnalytics: () => apiFetch<import("./types").Analytics>("/api/orders/analytics/"),
  getCashRegister: () => apiFetch<import("./types").CashRegisterState>("/api/orders/cash-register/"),
  setCashFloat: (amount: string) =>
    apiFetch<import("./types").CashRegisterState>("/api/orders/cash-register/", {
      method: "POST",
      body: JSON.stringify({ float_amount: amount }),
    }),
};
