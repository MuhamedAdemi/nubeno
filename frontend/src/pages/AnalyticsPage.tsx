import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useLang } from "../i18n/LangContext";
import { LanguageSwitcher } from "../components/LanguageSwitcher";

function formatEuro(value: string): string {
  return `${Number(value).toFixed(2)} €`;
}

function formatDate(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString(undefined, {
    weekday: "short",
    day: "2-digit",
    month: "2-digit",
  });
}

export function AnalyticsPage() {
  const { t } = useLang();
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({ queryKey: ["analytics"], queryFn: api.getAnalytics });

  const maxDaily = Math.max(1, ...(data?.daily.map((d) => Number(d.total)) ?? [0]));

  return (
    <div className="page">
      <header className="page-header">
        <button className="btn btn-ghost" onClick={() => navigate("/")}>
          ← {t("back_to_tables")}
        </button>
        <div className="header-actions">
          <LanguageSwitcher />
        </div>
      </header>

      <h1>{t("analytics_title")}</h1>

      {isLoading && <p>...</p>}

      {data && (
        <>
          <div className="stat-tile-row">
            <div className="stat-tile">
              <span className="stat-tile-label">{t("today")}</span>
              <span className="stat-tile-value">{formatEuro(data.today_total)}</span>
            </div>
            <div className="stat-tile">
              <span className="stat-tile-label">{t("this_week")}</span>
              <span className="stat-tile-value">{formatEuro(data.week_total)}</span>
            </div>
            <div className="stat-tile">
              <span className="stat-tile-label">{t("this_month")}</span>
              <span className="stat-tile-value">{formatEuro(data.month_total)}</span>
            </div>
            <div className="stat-tile stat-tile-accent">
              <span className="stat-tile-label">{t("all_time")}</span>
              <span className="stat-tile-value">{formatEuro(data.all_time_total)}</span>
            </div>
          </div>

          <h2 className="daily-breakdown-title">{t("daily_breakdown")}</h2>

          {data.daily.length === 0 && <p className="cart-empty">{t("no_sales_yet")}</p>}

          {data.daily.length > 0 && (
            <div className="daily-table">
              <div className="daily-table-header">
                <span>{t("date")}</span>
                <span>{t("orders_count")}</span>
                <span>{t("total")}</span>
              </div>
              {data.daily.map((row) => (
                <div key={row.date} className="daily-table-row">
                  <span className="daily-table-date">{formatDate(row.date)}</span>
                  <span className="daily-table-count">{row.order_count}</span>
                  <div className="daily-table-total-cell">
                    <span
                      className="daily-bar"
                      style={{ width: `${(Number(row.total) / maxDaily) * 100}%` }}
                    />
                    <span className="daily-table-total-value">{formatEuro(row.total)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
