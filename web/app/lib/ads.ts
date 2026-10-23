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

export const AD_SLOTS: Record<string, Ad[]> = {
  default: [],
};

export function pickAd(themeSlug?: string | null): Ad | null {
  const key = themeSlug?.trim().toLowerCase();
  const themed = key ? AD_SLOTS[key] : undefined;

  if (themed && themed.length > 0) {
    return themed[0];
  }

  const pool = Object.values(AD_SLOTS).flat();

  if (pool.length === 0) {
    return null;
  }

  return pool[Math.floor(Math.random() * pool.length)];
}
