import { useState } from "react";
import type { Order, OrderItem } from "../api/types";
import { itemName } from "../api/types";
import { useLang } from "../i18n/LangContext";

interface Props {
  order: Order;
  onDeleteItem: (itemId: number) => void;
  onEditItem: (item: OrderItem) => void;
  onPay: (itemIds: number[]) => void;
  onCancelOrder: () => void;
  onPrintKitchen: () => void;
  onTransferClick: () => void;
  busy: boolean;
}

export function CartPanel({
  order,
  onDeleteItem,
  onEditItem,
  onPay,
  onCancelOrder,
  onPrintKitchen,
  onTransferClick,
  busy,
}: Props) {
  const { lang, t } = useLang();
  const [selected, setSelected] = useState<Set<number>>(new Set());

  const unpaidItems = order.items.filter((item) => !item.is_paid);
  const selectedItems = unpaidItems.filter((item) => selected.has(item.id));
  const payTotal = selectedItems.length > 0 ? selectedItems : unpaidItems;
  const payAmount = payTotal.reduce((sum, item) => sum + Number(item.line_total), 0);

  function toggleSelected(itemId: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(itemId)) next.delete(itemId);
      else next.add(itemId);
      return next;
    });
  }

  function handlePay() {
    onPay(selectedItems.map((item) => item.id));
    setSelected(new Set());
  }

  return (
    <aside className="cart-panel">
      <h2>
        {t("cart_title")} — {t("table")} {order.table_number}
      </h2>

      {order.items.length === 0 && <p className="cart-empty">{t("cart_empty")}</p>}

      <ul className="cart-list">
        {order.items.map((item) => (
          <li key={item.id} className={item.is_paid ? "cart-item cart-item-paid" : "cart-item"}>
            <div className="cart-item-main">
              {!item.is_paid && (
                <input
                  type="checkbox"
                  className="cart-item-checkbox"
                  checked={selected.has(item.id)}
                  onChange={() => toggleSelected(item.id)}
                  disabled={busy}
                />
              )}
              <span className="cart-item-name">
                {item.quantity}× {itemName(item.menu_item, lang)}
                {item.menu_item.variant_label ? ` (${item.menu_item.variant_label})` : ""}
              </span>
              <span className="cart-item-price">{Number(item.line_total).toFixed(2)} €</span>
            </div>
            {item.removed_modifiers.length > 0 && (
              <div className="cart-item-mods">
                {item.removed_modifiers.map((m) => `${t("without")} ${itemName(m, lang)}`).join(", ")}
              </div>
            )}
            {item.note && <div className="cart-item-note">{item.note}</div>}
            {item.is_paid ? (
              <span className="paid-badge">✓ {t("paid")}</span>
            ) : (
              <div className="cart-item-actions">
                <button className="btn btn-ghost-small" onClick={() => onEditItem(item)} disabled={busy}>
                  {t("customize")}
                </button>
                <button className="btn btn-danger-ghost" onClick={() => onDeleteItem(item.id)} disabled={busy}>
                  {t("delete_item")}
                </button>
              </div>
            )}
          </li>
        ))}
      </ul>

      <div className="cart-total">
        <span>{t("total")}</span>
        <span>{Number(order.total).toFixed(2)} €</span>
      </div>
      {Number(order.remaining_total) !== Number(order.total) && (
        <div className="cart-total cart-total-remaining">
          <span>{t("remaining")}</span>
          <span>{Number(order.remaining_total).toFixed(2)} €</span>
        </div>
      )}

      <div className="cart-actions">
        <button className="btn btn-ghost btn-lg" onClick={onPrintKitchen} disabled={busy || order.items.length === 0}>
          {t("print_kitchen")}
        </button>
        <button className="btn btn-primary btn-lg" onClick={handlePay} disabled={busy || unpaidItems.length === 0}>
          {selectedItems.length > 0 ? `${t("pay_selected")} (${payAmount.toFixed(2)} €)` : `${t("pay")} (${payAmount.toFixed(2)} €)`}
        </button>
        <button className="btn btn-ghost btn-lg" onClick={onTransferClick} disabled={busy}>
          {t("transfer_table")}
        </button>
        <button className="btn btn-danger btn-lg" onClick={onCancelOrder} disabled={busy}>
          {t("cancel_order")}
        </button>
      </div>
    </aside>
  );
}
