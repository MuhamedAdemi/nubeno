import { useLang } from "../i18n/LangContext";
import type { Lang } from "../api/types";

const LANGS: { code: Lang; label: string }[] = [
  { code: "sq", label: "SQ" },
  { code: "hr", label: "HR" },
  { code: "en", label: "EN" },
];

export function LanguageSwitcher() {
  const { lang, setLang } = useLang();
  return (
    <div className="lang-switcher">
      {LANGS.map((l) => (
        <button
          key={l.code}
          className={l.code === lang ? "lang-btn active" : "lang-btn"}
          onClick={() => setLang(l.code)}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
