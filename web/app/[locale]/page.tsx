"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import Navbar from "@/app/components/Navbar";
import Logo from "@/app/components/Logo";
import { useLang } from "@/app/lib/lang";

export default function Home() {
  const { t, path } = useLang();

  const [query, setQuery] = useState("");

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      return;
    }

    window.location.href = path(
      `/search?q=${encodeURIComponent(trimmedQuery)}`
    );
  }

  return (
    <main className="min-h-screen bg-white text-gray-900">
      <div className="flex min-h-screen flex-col">
        <header className="flex items-center justify-between px-6 py-5">
          <Link
            href={path("/lists")}
            className="text-sm text-gray-600 transition hover:text-gray-900"
          >
            {t.home.exploreLists}
          </Link>

          <Navbar />
        </header>

        <section className="flex flex-1 flex-col items-center justify-center px-6 pb-32">
          <div className="w-full max-w-3xl text-center">
            <div className="mb-4 flex justify-center text-gray-900">
              <Logo className="h-16 w-16" />
            </div>

            <h1 className="mb-3 text-5xl font-semibold tracking-tight sm:text-6xl">
              Organic Rankings
            </h1>

            <p className="mb-4 text-base text-gray-500 sm:text-lg">
              {t.home.tagline}
            </p>

            <p className="mx-auto mb-10 max-w-2xl text-sm leading-6 text-gray-500">
              {t.home.intro}
            </p>

            <form
              onSubmit={handleSearch}
              className="mx-auto flex w-full max-w-2xl items-center rounded-full border border-gray-300 bg-white px-5 py-2 shadow-sm transition focus-within:border-gray-400 focus-within:shadow-md"
            >
              <span className="mr-3 text-xl text-gray-400">⌕</span>

              <input
                type="text"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={t.home.searchPlaceholder}
                className="min-w-0 flex-1 bg-transparent py-3 text-base outline-none placeholder:text-gray-400"
                aria-label={t.home.searchAria}
              />

              <button
                type="submit"
                className="ml-3 rounded-full bg-gray-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-gray-700"
              >
                {t.common.search}
              </button>
            </form>
          </div>
        </section>

        <footer className="border-t border-gray-100 px-6 py-5 text-center text-xs text-gray-400">
          Organic Rankings · {t.home.rankedByHumans} ·{" "}
          <Link
            href={path("/about")}
            className="hover:text-gray-600 hover:underline"
          >
            {t.home.about}
          </Link>
        </footer>
      </div>
    </main>
  );
}
