import type { PaymentMethod } from "../api/types";
import { useLang } from "../i18n/LangContext";

interface Props {
  onClose: () => void;
  onChoose: (method: PaymentMethod) => void;
}

export function PaymentMethodModal({ onClose, onChoose }: Props) {
  const { t } = useLang();
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
        <button className="btn btn-ghost btn-lg" onClick={onClose}>
          {t("close")}
        </button>
      </div>
    </div>
  );
}
