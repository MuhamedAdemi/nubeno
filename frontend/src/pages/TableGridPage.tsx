import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Table } from "../api/types";
import { useLang } from "../i18n/LangContext";
import { useAuth } from "../auth/AuthContext";
import { LanguageSwitcher } from "../components/LanguageSwitcher";

// Table transfer can be started right from the grid two ways: drag an
// occupied tile onto a free one with a mouse, or tap the tile's small
// transfer handle then tap the destination — the handle keeps this
// separate from the tile's normal "open this table" tap/click.
const DRAG_MIME = "application/x-nubeno-order-id";

export function TableGridPage() {
  const { t } = useLang();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [transferSource, setTransferSource] = useState<Table | null>(null);

  const { data: tables, isLoading } = useQuery({
    queryKey: ["tables"],
    queryFn: api.getTables,
    refetchInterval: 5000,
  });

  const transferMutation = useMutation({
    mutationFn: ({ orderId, tableId }: { orderId: number; tableId: number }) =>
      api.transferOrder(orderId, tableId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tables"] });
      setTransferSource(null);
    },
  });

  const setLocationMutation = useMutation({
    mutationFn: ({ tableId, locationNote }: { tableId: number; locationNote: string }) =>
      api.setTableLocation(tableId, locationNote),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tables"] }),
  });

  function completeTransfer(sourceOrderId: number, destinationTableId: number) {
    transferMutation.mutate({ orderId: sourceOrderId, tableId: destinationTableId });
  }

  function editLocation(table: Table) {
    const value = window.prompt(t("location_prompt"), table.location_note);
    if (value !== null) setLocationMutation.mutate({ tableId: table.id, locationNote: value.trim() });
  }

  const helperTables = (tables ?? []).filter((table) => table.is_helper);

  return (
    <div className="page">
      <div className="pos-topbar">
        <span className="pos-topbar-icon">N</span>
        <span className="pos-topbar-brand">NUBENO</span>
      </div>
      <header className="page-header">
        <div className="brand">nubeno</div>
        <div className="header-actions">
          <LanguageSwitcher />
          <button className="btn btn-ghost" onClick={() => navigate("/cash-register")}>
            {t("cash_register")}
          </button>
          {user?.is_admin && (
            <button className="btn btn-ghost" onClick={() => navigate("/analytics")}>
              {t("analytics")}
            </button>
          )}
          <span className="username">{user?.username}</span>
          <button className="btn btn-ghost" onClick={logout}>
            {t("logout")}
          </button>
        </div>
      </header>

      <h1>{t("tables_title")}</h1>

      {isLoading && <p>...</p>}

      {transferSource && (
        <div className="transfer-hint-banner">
          <span>
            {t("transfer_table")} — {t("table")} {transferSource.number}: {t("pick_destination_table")}
          </span>
          <button className="btn btn-ghost-small" onClick={() => setTransferSource(null)}>
            {t("cancel")}
          </button>
        </div>
      )}

      <div className="table-grid">{tables?.filter((table) => !table.is_helper).map(renderTile)}</div>

      {helperTables.length > 0 && (
        <>
          <h2 className="helper-tables-title">{t("helper_tables_title")}</h2>
          <p className="modifier-hint">{t("helper_tables_hint")}</p>
          <div className="table-grid">{helperTables.map(renderTile)}</div>
        </>
      )}
    </div>
  );

  function renderTile(table: Table) {
    const isOccupied = table.status === "OCCUPIED";
    const isTransferSource = transferSource?.id === table.id;

    function handleClick() {
      if (transferSource && !isOccupied) {
        completeTransfer(transferSource.open_order_id!, table.id);
        return;
      }
      if (!transferSource) navigate(`/tables/${table.id}`);
    }

    return (
      <div
        key={table.id}
        role="button"
        tabIndex={0}
        className={[
          "table-tile",
          isOccupied ? "occupied" : "free",
          isTransferSource ? "selected-for-transfer" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        draggable={isOccupied}
        onDragStart={(e) => {
          if (!table.open_order_id) return;
          e.dataTransfer.setData(DRAG_MIME, String(table.open_order_id));
        }}
        onDragOver={(e) => {
          if (!isOccupied) e.preventDefault();
        }}
        onDrop={(e) => {
          if (isOccupied) return;
          const orderId = Number(e.dataTransfer.getData(DRAG_MIME));
          if (orderId) completeTransfer(orderId, table.id);
        }}
        onClick={handleClick}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") handleClick();
        }}
      >
        {isOccupied && (
          <button
            className="table-transfer-handle"
            title={t("transfer_table")}
            onClick={(e) => {
              e.stopPropagation();
              setTransferSource(isTransferSource ? null : table);
            }}
          >
            ⇄
          </button>
        )}
        {table.is_helper && (
          <button
            className="table-location-handle"
            title={t("location_prompt")}
            onClick={(e) => {
              e.stopPropagation();
              editLocation(table);
            }}
          >
            📍
          </button>
        )}
        <span className="table-number">{table.label || `${t("table")} ${table.number}`}</span>
        <span className="table-status">{isOccupied ? t("occupied") : t("free")}</span>
        {table.location_note && <span className="table-location-note">→ {table.location_note}</span>}
        {table.open_order_total && (
          <span className="table-total">{Number(table.open_order_total).toFixed(2)} €</span>
        )}
      </div>
    );
  }
}
