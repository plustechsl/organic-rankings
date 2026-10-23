export type Ad = {
  id: string;
  title: string;
  text?: string;
  imageUrl?: string;
  href?: string;
  alt?: string;
  iframeSrc?: string;
  html?: string;
};

export const DEFAULT_AD_SLOT = "default";

export const AD_SLOTS: Record<string, Ad[]> = {
  default: [],
};

export function pickAd(themeSlug?: string | null): Ad | null {
  const key = themeSlug?.trim().toLowerCase() || DEFAULT_AD_SLOT;
  const ads = AD_SLOTS[key] ?? AD_SLOTS[DEFAULT_AD_SLOT];

  return ads?.[0] ?? null;
}
