export type Lang = "hr" | "en" | "sq";

export interface ModifierOption {
  id: number;
  name_hr: string;
  name_en: string;
  name_sq: string;
}

export interface ModifierGroup {
  id: number;
  name_hr: string;
  name_en: string;
  name_sq: string;
  options: ModifierOption[];
}

export interface MenuItem {
  id: number;
  name_hr: string;
  name_en: string;
  name_sq: string;
  variant_label: string;
  price: string;
  modifier_group: ModifierGroup | null;
}

export interface Category {
  id: number;
  name_hr: string;
  name_en: string;
  name_sq: string;
  group: "FOOD" | "DRINK";
  items: MenuItem[];
}

export interface Table {
  id: number;
  number: number;
  status: "FREE" | "OCCUPIED";
  open_order_id: number | null;
  open_order_total: string | null;
}

export type PaymentMethod = "CASH" | "CARD" | "MIXED";

export interface OrderItem {
  id: number;
  menu_item: MenuItem;
  quantity: number;
  unit_price: string;
  note: string;
  removed_modifiers: ModifierOption[];
  line_total: string;
  is_paid: boolean;
  payment_method: PaymentMethod | null;
}

export interface Order {
  id: number;
  table: number;
  table_number: number;
  status: "OPEN" | "PAID" | "CANCELLED";
  opened_by: number | null;
  opened_at: string;
  closed_at: string | null;
  items: OrderItem[];
  total: string;
  remaining_total: string;
}

export interface PayResult extends Order {
  paid_item_ids: number[];
}

export interface DailySales {
  date: string;
  order_count: number;
  total: string;
}

export interface Analytics {
  today_total: string;
  week_total: string;
  month_total: string;
  all_time_total: string;
  daily: DailySales[];
}

export interface CashRegisterState {
  float_amount: string;
  set_at: string | null;
  set_by_username: string | null;
  cash_total: string;
  card_total: string;
  expected_cash: string;
}

export function itemName(item: { name_hr: string; name_en: string; name_sq: string }, lang: Lang): string {
  return item[`name_${lang}`] || item.name_hr;
}
