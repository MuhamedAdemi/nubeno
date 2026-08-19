import { createContext, useContext, useState, type ReactNode } from "react";
import type { Lang } from "../api/types";
import { t as translate, type TranslationKey } from "./translations";

interface LangContextValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: TranslationKey) => string;
}

const LangContext = createContext<LangContextValue | null>(null);

const LANG_KEY = "nubeno_lang";

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    return (localStorage.getItem(LANG_KEY) as Lang) || "sq";
  });

  function setLang(l: Lang) {
    localStorage.setItem(LANG_KEY, l);
    setLangState(l);
  }

  return (
    <LangContext.Provider value={{ lang, setLang, t: (key) => translate(key, lang) }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  const ctx = useContext(LangContext);
  if (!ctx) throw new Error("useLang must be used within LangProvider");
  return ctx;
}
