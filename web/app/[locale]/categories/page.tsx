"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Navbar from "@/app/components/Navbar";
import Logo from "@/app/components/Logo";
import { api } from "@/app/lib/api";
import { useLang } from "@/app/lib/lang";
import { Category } from "@/app/lib/types";

function normalize(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function categoryHref(category: Category): string {
  return `/search?q=${encodeURIComponent(`categoria:${category.slug}`)}`;
}

function tagHref(category: Category, tag: string): string {
  return `/search?q=${encodeURIComponent(
    `categoria:${category.slug} #${tag}`
  )}`;
}

export default function CategoriesPage() {
  const { t, locale, path } = useLang();

  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    api
      .get<Category[]>("/categories", { lang: locale })
      .then(setCategories)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [locale]);

  const normalizedQuery = normalize(query.trim());

  const filtered = categories
    .map((category) => {
      const matchesCategory = normalize(category.name).includes(normalizedQuery);
      const matchingTags = category.tags.filter((tag) =>
        normalize(tag).includes(normalizedQuery)
      );

      return {
        category,
        tags: matchesCategory ? category.tags : matchingTags,
        matches: matchesCategory || matchingTags.length > 0,
      };
    })
    .filter((entry) => entry.matches);

  return (
    <main className="min-h-screen bg-white text-gray-900">
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-5">
          <Link
            href={path("/")}
            className="flex flex-shrink-0 items-center gap-2 text-xl font-semibold tracking-tight"
          >
            <Logo className="h-6 w-6" />
            Organic Rankings
          </Link>

          <Navbar />
        </div>
      </header>

      <section className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-6 text-2xl font-semibold">{t.categories.title}</h1>

        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={t.categories.searchPlaceholder}
          className="mb-8 w-full rounded-full border border-gray-300 px-5 py-2.5 text-sm outline-none focus:border-gray-500"
        />

        {loading && <p className="text-sm text-gray-500">{t.common.loading}</p>}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {t.categories.errorLoad}
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <p className="text-sm text-gray-500">
            {categories.length === 0
              ? t.categories.empty
              : t.categories.noMatch}
          </p>
        )}

        {!loading && !error && filtered.length > 0 && (
          <div className="space-y-6">
            {filtered.map(({ category, tags }) => (
              <article
                key={category.id}
                className="rounded-lg border border-gray-200 p-5"
              >
                <h2 className="mb-3 text-lg font-medium">
                  <Link
                    href={path(categoryHref(category))}
                    className="text-blue-700 hover:underline"
                  >
                    {category.name}
                  </Link>
                </h2>

                {tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {tags.map((tag) => (
                      <Link
                        key={tag}
                        href={path(tagHref(category, tag))}
                        className="rounded-full border border-gray-300 px-3 py-1.5 text-sm text-gray-700 transition hover:border-gray-500"
                      >
                        {tag}
                      </Link>
                    ))}
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
