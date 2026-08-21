import { useState } from "react";
import type { PaymentMethod } from "../api/types";
import { useLang } from "../i18n/LangContext";

interface Props {
  total: number;
  onClose: () => void;
  onChoose: (method: PaymentMethod, cashAmount?: number) => void;
}

export function PaymentMethodModal({ total, onClose, onChoose }: Props) {
  const { t } = useLang();
  const [pickingCashAmount, setPickingCashAmount] = useState(false);
  const [cashAmount, setCashAmount] = useState("");

  const cashAmountNumber = Number(cashAmount);
  const cashAmountValid =
    cashAmount !== "" && !Number.isNaN(cashAmountNumber) && cashAmountNumber >= 0 && cashAmountNumber <= total;

  if (pickingCashAmount) {
    return (
      <div className="modal-backdrop" onClick={onClose}>
        <div className="modal payment-method-modal" onClick={(e) => e.stopPropagation()}>
          <h2>{t("cash_amount_label")}</h2>
          <p className="modifier-hint">
            {total.toFixed(2)} € {t("of_total")}
          </p>
          <input
            className="cash-amount-input"
            type="number"
            inputMode="decimal"
            step="0.01"
            min="0"
            max={total}
            autoFocus
            placeholder="0.00"
            value={cashAmount}
            onChange={(e) => setCashAmount(e.target.value)}
          />
          {cashAmount !== "" && !cashAmountValid && (
            <p className="error-text">{t("cash_amount_too_high")}</p>
          )}
          <div className="modal-actions">
            <button className="btn btn-ghost" onClick={() => setPickingCashAmount(false)}>
              {t("back")}
            </button>
            <button
              className="btn btn-primary"
              disabled={!cashAmountValid}
              onClick={() => onChoose("MIXED", cashAmountNumber)}
            >
              {t("confirm")}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal payment-method-modal" onClick={(e) => e.stopPropagation()}>
        <h2>{t("choose_payment_method")}</h2>
        <div className="payment-method-options">
          <button className="btn btn-primary btn-lg" onClick={() => onChoose("CASH")}>
            {t("cash")}
          </button>
          <button className="btn btn-primary btn-lg" onClick={() => onChoose("CARD")}>
            {t("card")}
          </button>
        </div>
        <button className="btn btn-primary btn-lg payment-method-mixed" onClick={() => setPickingCashAmount(true)}>
          {t("card_plus_cash")}
        </button>
        <button className="btn btn-ghost btn-lg" onClick={onClose}>
          {t("close")}
        </button>
      </div>
    </div>
  );
}
