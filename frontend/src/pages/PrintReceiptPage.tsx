import { useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { itemName } from "../api/types";
import { useLang } from "../i18n/LangContext";
import { useAuth } from "../auth/AuthContext";

export function PrintReceiptPage() {
  const { orderId } = useParams();
  const [searchParams] = useSearchParams();
  const { lang, t } = useLang();
  const { user } = useAuth();
  const navigate = useNavigate();

  const { data: order } = useQuery({
    queryKey: ["order", Number(orderId)],
    queryFn: () => api.getOrder(Number(orderId)),
    enabled: !!orderId,
  });

  // Reached two ways: after actually paying (auto-prints, as before), or
  // from the new non-destructive "Shiko Faturën" button on an unpaid order —
  // that one is just a nice on-screen bill and must never trigger a print.
  const isPreview = searchParams.get("preview") === "1";

  useEffect(() => {
    if (order && !isPreview) {
      const timer = setTimeout(() => window.print(), 300);
      return () => clearTimeout(timer);
    }
  }, [order, isPreview]);

  if (!order) return null;

  const itemsParam = searchParams.get("items");
  const batchIds = itemsParam ? itemsParam.split(",").map(Number) : null;
  const items = batchIds ? order.items.filter((item) => batchIds.includes(item.id)) : order.items;
  const batchTotal = items.reduce((sum, item) => sum + Number(item.line_total), 0);

  return (
    <div className="receipt-page">
      {/* Screen-only: a nicer branded preview for showing the guest on the
          phone. Never printed — the physical receipt below stays minimal. */}
      <div className="receipt-screen-header no-print">
        <div className="receipt-screen-brand">nubeno</div>
      </div>

      <div className="receipt">
        <div className="receipt-header">
          <div>
            {t("table")} {order.table_number} — #{order.id}
          </div>
          <div className="receipt-date">{new Date().toLocaleString()}</div>
          <div className="receipt-meta">{user?.initials}</div>
        </div>
        <hr />
        {items.map((item) => (
          <div key={item.id} className="receipt-item">
            <div className="receipt-item-line">
              <span>
                {itemName(item.menu_item, lang)}
                {item.menu_item.variant_label ? ` (${item.menu_item.variant_label})` : ""}
              </span>
            </div>
            <div className="receipt-item-line receipt-item-line-qty">
              {item.quantity > 1 ? (
                <span>
                  {item.quantity} x {Number(item.unit_price).toFixed(2)} € = {Number(item.line_total).toFixed(2)} €
                </span>
              ) : (
                <span>{Number(item.line_total).toFixed(2)} €</span>
              )}
            </div>
            {item.removed_modifiers.length > 0 && (
              <div className="receipt-item-mods">
                {item.removed_modifiers.map((m) => `${t("without").toUpperCase()} ${itemName(m, lang).toUpperCase()}`).join(", ")}
              </div>
            )}
            {item.note && <div className="receipt-item-mods">{item.note.toUpperCase()}</div>}
          </div>
        ))}
        <hr />
        <div className="receipt-total">
          <span>{t("total")}</span>
          <span>{batchTotal.toFixed(2)} €</span>
        </div>
      </div>

      {/* Screen-only footer: barcode + thank-you, purely decorative. */}
      <div className="receipt-screen-footer no-print">
        <div className="receipt-barcode" />
        <div className="receipt-screen-thanks">Faleminderit! / Hvala! / Thank you!</div>
      </div>

      <div className="no-print receipt-actions">
        <button className="btn btn-primary" onClick={() => window.print()}>
          {t("print_receipt")}
        </button>
        <button
          className="btn btn-ghost"
          onClick={() => (order.status === "OPEN" ? navigate(`/tables/${order.table}`) : navigate("/"))}
        >
          {order.status === "OPEN" ? t("back_to_order") : t("back_to_tables")}
        </button>
      </div>
    </div>
  );
}
