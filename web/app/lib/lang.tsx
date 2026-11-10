"use client";

import { createContext, useContext } from "react";
import type { Dictionary } from "./dictionaries";
import { localePath, type Locale } from "./i18n";

type LangContextValue = {
  locale: Locale;
  t: Dictionary;
  path: (href: string) => string;
};

const LangContext = createContext<LangContextValue | null>(null);

export function LangProvider({
  locale,
  dictionary,
  children,
}: {
  locale: Locale;
  dictionary: Dictionary;
  children: React.ReactNode;
}) {
  const value: LangContextValue = {
    locale,
    t: dictionary,
    path: (href: string) => localePath(locale, href),
  };

  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export function useLang(): LangContextValue {
  const context = useContext(LangContext);

  if (!context) {
    throw new Error("useLang must be used inside LangProvider");
  }

  return context;
}
