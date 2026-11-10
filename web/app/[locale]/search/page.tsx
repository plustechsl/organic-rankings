import { Suspense } from "react";
import { isLocale } from "@/app/lib/i18n";
import { getDictionary } from "@/app/lib/dictionaries";
import SearchClient from "./SearchClient";

type PageParams = { params: Promise<{ locale: string }> };

export default async function Page({ params }: PageParams) {
  const { locale } = await params;

  if (!isLocale(locale)) {
    return null;
  }

  const t = getDictionary(locale);

  return (
    <Suspense
      fallback={<div className="p-6">{t.common.loading}</div>}
    >
      <SearchClient />
    </Suspense>
  );
}
