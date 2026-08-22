import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { OrderItem } from "../api/types";
import { itemName } from "../api/types";
import { useLang } from "../i18n/LangContext";
import { useAuth } from "../auth/AuthContext";

export function KitchenPrintPage() {
  const { orderId } = useParams();
  const { lang, t } = useLang();
  const { user } = useAuth();
  const navigate = useNavigate();

  const { data: order } = useQuery({
    queryKey: ["order", Number(orderId)],
    queryFn: () => api.getOrder(Number(orderId)),
    enabled: !!orderId,
  });

  useEffect(() => {
    if (order) {
      const timer = setTimeout(() => window.print(), 300);
      return () => clearTimeout(timer);
    }
  }, [order]);

  if (!order) return null;

  // Drinks print above food as one group, in a separate section from food —
  // stable sort keeps each group's own item order (the order they were
  // added) intact.
  const drinks = order.items.filter((item) => item.menu_item.category_group === "DRINK");
  const food = order.items.filter((item) => item.menu_item.category_group === "FOOD");

  function renderItem(item: OrderItem) {
    return (
      <div key={item.id} className="receipt-item">
        <div className="receipt-item-line receipt-item-line-kitchen">
          <span>
            {item.quantity}× {itemName(item.menu_item, lang)}
            {item.menu_item.variant_label ? ` (${item.menu_item.variant_label})` : ""}
          </span>
        </div>
        {item.removed_modifiers.length > 0 && (
          <div className="receipt-item-mods">
            {item.removed_modifiers.map((m) => `${t("without").toUpperCase()} ${itemName(m, lang).toUpperCase()}`).join(", ")}
          </div>
        )}
        {item.note && <div className="receipt-item-note-kitchen">{item.note.toUpperCase()}</div>}
      </div>
    );
  }

  return (
    <div className="receipt-page">
      <div className="receipt">
        <div className="receipt-header">
          <div>{t("kitchen_ticket_title")}</div>
          <div>
            {order.table_label || `${t("table")} ${order.table_number}`} — #{order.id}
          </div>
          {order.table_location_note && (
            <div className="receipt-location-note">→ {order.table_location_note}</div>
          )}
          <div className="receipt-date">{new Date().toLocaleString()}</div>
          <div className="receipt-meta">{user?.initials}</div>
        </div>
        <hr />
        {drinks.length > 0 && (
          <>
            <div className="receipt-section-label">{t("drinks")}</div>
            {drinks.map(renderItem)}
            <hr />
          </>
        )}
        {food.length > 0 && (
          <>
            <div className="receipt-section-label">{t("food")}</div>
            {food.map(renderItem)}
          </>
        )}
      </div>

      <div className="no-print receipt-actions">
        <button className="btn btn-primary" onClick={() => window.print()}>
          {t("print_kitchen")}
        </button>
        <button className="btn btn-ghost" onClick={() => navigate(`/tables/${order.table}`)}>
          {t("back_to_order")}
        </button>
      </div>
    </div>
  );
}
