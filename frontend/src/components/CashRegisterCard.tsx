import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { useLang } from "../i18n/LangContext";
import { useAuth } from "../auth/AuthContext";

function formatEuro(value: string): string {
  return `${Number(value).toFixed(2)} €`;
}

export function CashRegisterCard() {
  const { t } = useLang();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [floatInput, setFloatInput] = useState("");

  const { data } = useQuery({ queryKey: ["cash-register"], queryFn: api.getCashRegister });

  const setFloatMutation = useMutation({
    mutationFn: (amount: string) => api.setCashFloat(amount),
    onSuccess: () => {
      setFloatInput("");
      queryClient.invalidateQueries({ queryKey: ["cash-register"] });
    },
  });

  if (!data) return null;

  return (
    <div className="cash-register-card">
      <div className="stat-tile-row">
        <div className="stat-tile">
          <span className="stat-tile-label">{t("starting_float")}</span>
          <span className="stat-tile-value">{formatEuro(data.float_amount)}</span>
          {data.set_by_username ? (
            <span className="cash-register-meta">
              {t("float_set_by")} {data.set_by_username}
              {data.set_at ? ` — ${new Date(data.set_at).toLocaleString()}` : ""}
            </span>
          ) : (
            <span className="cash-register-meta">{t("no_float_set")}</span>
          )}
        </div>
        <div className="stat-tile">
          <span className="stat-tile-label">{t("cash_total")}</span>
          <span className="stat-tile-value">{formatEuro(data.cash_total)}</span>
        </div>
        <div className="stat-tile">
          <span className="stat-tile-label">{t("card_total")}</span>
          <span className="stat-tile-value">{formatEuro(data.card_total)}</span>
        </div>
        <div className="stat-tile stat-tile-accent">
          <span className="stat-tile-label">{t("expected_cash")}</span>
          <span className="stat-tile-value">{formatEuro(data.expected_cash)}</span>
        </div>
      </div>

      {user?.is_admin && (
        <form
          className="cash-register-set-form"
          onSubmit={(e) => {
            e.preventDefault();
            if (floatInput) setFloatMutation.mutate(floatInput);
          }}
        >
          <input
            type="number"
            inputMode="decimal"
            step="0.01"
            min="0"
            placeholder="100.00"
            value={floatInput}
            onChange={(e) => setFloatInput(e.target.value)}
          />
          <button className="btn btn-primary" type="submit" disabled={!floatInput || setFloatMutation.isPending}>
            {t("set_float")}
          </button>
        </form>
      )}
    </div>
  );
}
