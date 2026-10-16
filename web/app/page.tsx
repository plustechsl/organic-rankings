"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import Navbar from "@/app/components/Navbar";
import Logo from "@/app/components/Logo";

export default function Home() {
  const [query, setQuery] = useState("");

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      return;
    }

    window.location.href = `/search?q=${encodeURIComponent(trimmedQuery)}`;
  }

  return (
    <main className="min-h-screen bg-white text-gray-900">
      <div className="flex min-h-screen flex-col">
        <header className="flex items-center justify-between px-6 py-5">
          <Link href="/lists" className="text-sm text-gray-600 transition hover:text-gray-900">
            Explorar listas
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
              Donde el ranking lo decide la gente, no un algoritmo opaco.
            </p>

            <p className="mx-auto mb-10 max-w-2xl text-sm leading-6 text-gray-500">
              Organic Rankings es una plataforma abierta de listas de recursos web
              ordenadas por personas. La puntuación de cada recurso la decide la
              comunidad: no un algoritmo opaco, ni técnicas de SEO, ni quien más
              paga.
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
                placeholder="Buscar en Internet..."
                className="min-w-0 flex-1 bg-transparent py-3 text-base outline-none placeholder:text-gray-400"
                aria-label="Buscar"
              />

              <button
                type="submit"
                className="ml-3 rounded-full bg-gray-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-gray-700"
              >
                Buscar
              </button>
            </form>
          </div>
        </section>

        <footer className="border-t border-gray-100 px-6 py-5 text-center text-xs text-gray-400">
          Organic Rankings · Puntuado por humanos ·{" "}
          <Link href="/about" className="hover:text-gray-600 hover:underline">
            Sobre el proyecto
          </Link>
        </footer>
      </div>
    </main>
  );
}
