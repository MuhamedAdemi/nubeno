import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useLang } from "../i18n/LangContext";
import { useAuth } from "../auth/AuthContext";
import { LanguageSwitcher } from "../components/LanguageSwitcher";

export function TableGridPage() {
  const { t } = useLang();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const { data: tables, isLoading } = useQuery({
    queryKey: ["tables"],
    queryFn: api.getTables,
    refetchInterval: 5000,
  });

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
          <button className="btn btn-ghost" onClick={() => navigate("/analytics")}>
            {t("analytics")}
          </button>
          <span className="username">{user?.username}</span>
          <button className="btn btn-ghost" onClick={logout}>
            {t("logout")}
          </button>
        </div>
      </header>

      <h1>{t("tables_title")}</h1>

      {isLoading && <p>...</p>}

      <div className="table-grid">
        {tables?.map((table) => (
          <button
            key={table.id}
            className={`table-tile ${table.status === "OCCUPIED" ? "occupied" : "free"}`}
            onClick={() => navigate(`/tables/${table.id}`)}
          >
            <span className="table-number">
              {t("table")} {table.number}
            </span>
            <span className="table-status">
              {table.status === "OCCUPIED" ? t("occupied") : t("free")}
            </span>
            {table.open_order_total && (
              <span className="table-total">{Number(table.open_order_total).toFixed(2)} €</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
