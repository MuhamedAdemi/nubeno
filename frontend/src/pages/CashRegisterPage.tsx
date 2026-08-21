import { useNavigate } from "react-router-dom";
import { useLang } from "../i18n/LangContext";
import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { CashRegisterCard } from "../components/CashRegisterCard";

export function CashRegisterPage() {
  const { t } = useLang();
  const navigate = useNavigate();

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

      <h1>{t("cash_register")}</h1>

      <CashRegisterCard />
    </div>
  );
}
