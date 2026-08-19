import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useLang } from "../i18n/LangContext";
import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { ApiError } from "../api/client";

export function LoginPage() {
  const { login } = useAuth();
  const { t } = useLang();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(t("login_error"));
      } else {
        setError(String(err));
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-top">
          <div className="brand">nubeno</div>
          <LanguageSwitcher />
        </div>
        <h1>{t("login_title")}</h1>
        <form onSubmit={handleSubmit}>
          <label>
            {t("username")}
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
              autoComplete="username"
            />
          </label>
          <label>
            {t("password")}
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          {error && <div className="error-text">{error}</div>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {t("login_button")}
          </button>
        </form>
      </div>
    </div>
  );
}
