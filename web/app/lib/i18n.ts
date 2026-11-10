export const LOCALES = ["es", "en", "ca"] as const;

export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "es";

export const DATE_LOCALES: Record<Locale, string> = {
  es: "es-ES",
  en: "en-GB",
  ca: "ca-ES",
};

export function isLocale(value: string | undefined | null): value is Locale {
  return !!value && (LOCALES as readonly string[]).includes(value);
}

export function localePath(locale: Locale, href: string): string {
  const clean = href === "/" ? "" : href;

  return `/${locale}${clean}`;
}

export function format(
  template: string,
  values: Record<string, string | number>
): string {
  return template.replace(/\{(\w+)\}/g, (_, key: string) =>
    values[key] !== undefined ? String(values[key]) : ""
  );
}
