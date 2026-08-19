import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Order, OrderItem, PaymentMethod } from "../api/types";
import { itemName } from "../api/types";
import { useLang } from "../i18n/LangContext";
import { useAuth } from "../auth/AuthContext";
import { PaymentMethodModal } from "./PaymentMethodModal";

interface Props {
  order: Order;
  onDeleteItem: (itemId: number) => void;
  onEditItem: (item: OrderItem) => void;
  onPay: (itemIds: number[], paymentMethod: PaymentMethod) => void;
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
  const { user } = useAuth();
  const navigate = useNavigate();
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [showPaymentModal, setShowPaymentModal] = useState(false);

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

  function handleChoosePaymentMethod(method: PaymentMethod) {
    onPay(selectedItems.map((item) => item.id), method);
    setSelected(new Set());
    setShowPaymentModal(false);
  }

  // Non-destructive: shows the same nice on-screen bill without paying or
  // freeing the table — the owner specifically wanted a way to show the
  // guest a preview from the phone without committing to anything.
  function handleViewBill() {
    const ids = payTotal.map((item) => item.id).join(",");
    navigate(`/orders/${order.id}/print?items=${ids}&preview=1`);
  }

  return (
    <aside className="cart-panel">
      <div className="cart-table-header">
        <span></span>
        <span>{t("item_name_column")}</span>
        <span className="cart-col-qty">{t("quantity")}</span>
        <span className="cart-col-amount">{t("amount")}</span>
      </div>

      {order.items.length === 0 && <p className="cart-empty">{t("cart_empty")}</p>}

      <ul className="cart-list">
        {order.items.map((item) => (
          <li key={item.id} className={item.is_paid ? "cart-item cart-item-paid" : "cart-item"}>
            <div className="cart-item-main">
              {!item.is_paid ? (
                <input
                  type="checkbox"
                  className="cart-item-checkbox"
                  checked={selected.has(item.id)}
                  onChange={() => toggleSelected(item.id)}
                  disabled={busy}
                />
              ) : (
                <span />
              )}
              <span className="cart-item-name">
                {itemName(item.menu_item, lang)}
                {item.menu_item.variant_label ? ` (${item.menu_item.variant_label})` : ""}
              </span>
              <span className="cart-col-qty">{item.quantity}</span>
              <span className="cart-col-amount">{Number(item.line_total).toFixed(2)} €</span>
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

      <div className="cart-summary-bar">
        <span className="cart-summary-table">{t("table")} {order.table_number}</span>
        {user?.initials && <span className="cart-summary-waiter">{user.initials}</span>}
        <span className="cart-summary-total">{Number(order.total).toFixed(2)} €</span>
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
        <button className="btn btn-ghost btn-lg" onClick={handleViewBill} disabled={busy || unpaidItems.length === 0}>
          {t("view_bill")}
        </button>
        <button
          className="btn btn-primary btn-lg"
          onClick={() => setShowPaymentModal(true)}
          disabled={busy || unpaidItems.length === 0}
        >
          {selectedItems.length > 0 ? `${t("pay_selected")} (${payAmount.toFixed(2)} €)` : `${t("pay")} (${payAmount.toFixed(2)} €)`}
        </button>
        <button className="btn btn-ghost btn-lg" onClick={onTransferClick} disabled={busy}>
          {t("transfer_table")}
        </button>
        <button className="btn btn-danger btn-lg" onClick={onCancelOrder} disabled={busy}>
          {t("cancel_order")}
        </button>
      </div>

      {showPaymentModal && (
        <PaymentMethodModal onClose={() => setShowPaymentModal(false)} onChoose={handleChoosePaymentMethod} />
      )}
    </aside>
  );
}
