import type { MenuItem, ModifierOption } from "../api/types";
import { itemName } from "../api/types";
import { useLang } from "../i18n/LangContext";
import { useAuth } from "../auth/AuthContext";

export interface DraftItem {
  key: string;
  menuItem: MenuItem;
  quantity: number;
  removedOptions: ModifierOption[];
  note: string;
}

interface Props {
  tableNumber: number;
  items: DraftItem[];
  onDeleteItem: (key: string) => void;
  onEditItem: (item: DraftItem) => void;
  onRegister: () => void;
  busy: boolean;
}

export function DraftCartPanel({ tableNumber, items, onDeleteItem, onEditItem, onRegister, busy }: Props) {
  const { lang, t } = useLang();
  const { user } = useAuth();

  const total = items.reduce((sum, item) => sum + Number(item.menuItem.price) * item.quantity, 0);

  return (
    <aside className="cart-panel">
      <p className="draft-hint">{t("draft_hint")}</p>

      <div className="cart-table-header">
        <span></span>
        <span>{t("item_name_column")}</span>
        <span className="cart-col-qty">{t("quantity")}</span>
        <span className="cart-col-amount">{t("amount")}</span>
      </div>

      {items.length === 0 && <p className="cart-empty">{t("cart_empty")}</p>}

      <ul className="cart-list">
        {items.map((item) => (
          <li key={item.key} className="cart-item">
            <div className="cart-item-main">
              <span />
              <span className="cart-item-name">
                {itemName(item.menuItem, lang)}
                {item.menuItem.variant_label ? ` (${item.menuItem.variant_label})` : ""}
              </span>
              <span className="cart-col-qty">{item.quantity}</span>
              <span className="cart-col-amount">
                {(Number(item.menuItem.price) * item.quantity).toFixed(2)} €
              </span>
            </div>
            {item.removedOptions.length > 0 && (
              <div className="cart-item-mods">
                {item.removedOptions.map((m) => `${t("without")} ${itemName(m, lang)}`).join(", ")}
              </div>
            )}
            {item.note && <div className="cart-item-note">{item.note}</div>}
            <div className="cart-item-actions">
              <button className="btn btn-ghost-small" onClick={() => onEditItem(item)} disabled={busy}>
                {t("customize")}
              </button>
              <button className="btn btn-danger-ghost" onClick={() => onDeleteItem(item.key)} disabled={busy}>
                {t("delete_item")}
              </button>
            </div>
          </li>
        ))}
      </ul>

      <div className="cart-summary-bar">
        <span className="cart-summary-table">{t("table")} {tableNumber}</span>
        {user?.initials && <span className="cart-summary-waiter">{user.initials}</span>}
        <span className="cart-summary-total">{total.toFixed(2)} €</span>
      </div>

      <div className="cart-actions">
        <button className="btn btn-primary btn-lg" onClick={onRegister} disabled={busy || items.length === 0}>
          {t("register_table")}
        </button>
      </div>
    </aside>
  );
}
