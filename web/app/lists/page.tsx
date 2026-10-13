"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/app/components/Navbar";
import Logo from "@/app/components/Logo";
import { api, getToken, ApiRequestError } from "@/app/lib/api";
import { LinkList, Category } from "@/app/lib/types";

type CurrentUser = {
  id: number;
  username: string;
  email: string;
  role: string;
};

type SeedResult = {
  id: number;
  title: string;
  slug: string;
  description: string | null;
  category: string;
  links_created: number;
  tags: string[];
};

export default function ListsPage() {
  const router = useRouter();

  const [lists, setLists] = useState<LinkList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [query, setQuery] = useState("");

  const [showSeedForm, setShowSeedForm] = useState(false);
  const [seedTopic, setSeedTopic] = useState("");
  const [seedCategory, setSeedCategory] = useState("");
  const [seedMaxResults, setSeedMaxResults] = useState(8);
  const [seedError, setSeedError] = useState<string | null>(null);
  const [seedLoading, setSeedLoading] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);

  useEffect(() => {
    if (getToken()) {
      api
        .get<CurrentUser>("/auth/me")
        .then((me) => {
          setCurrentUser(me);
          if (me.role === "admin") {
            api.get<Category[]>("/categories").then(setCategories).catch(() => {});
          }
        })
        .catch(() => setCurrentUser(null));
    }

    async function fetchLists() {
      try {
        const data = await api.get<LinkList[]>("/lists");
        setLists(data);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    }

    fetchLists();
  }, []);

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmed = query.trim();

    if (!trimmed) {
      return;
    }

    router.push(`/search?q=${encodeURIComponent(trimmed)}`);
  }

  async function handleSeedSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSeedError(null);
    setSeedLoading(true);

    try {
      const result = await api.post<SeedResult>("/admin/seed-list", {
        topic: seedTopic,
        category_name: seedCategory || undefined,
        max_results: seedMaxResults,
      });

      router.push(`/lists/${result.slug}`);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setSeedError(err.message);
      } else {
        setSeedError("No se pudo generar la lista.");
      }
    } finally {
      setSeedLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-white text-gray-900">
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-6xl items-center gap-8 px-6 py-5">
          <Link
            href="/"
            className="flex flex-shrink-0 items-center gap-2 text-xl font-semibold tracking-tight"
          >
            <Logo className="h-6 w-6" />
            Organic Rankings
          </Link>

          <form
            onSubmit={handleSearch}
            className="flex max-w-2xl flex-1 items-center rounded-full border border-gray-300 px-4 py-1.5"
          >
            <span className="mr-3 text-lg text-gray-400">⌕</span>

            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar listas y enlaces... prueba #python"
              className="min-w-0 flex-1 bg-transparent py-2 outline-none"
            />

            <button
              type="submit"
              className="rounded-full bg-gray-900 px-5 py-2 text-sm font-medium text-white hover:bg-gray-700"
            >
              Buscar
            </button>
          </form>

          <Navbar />
        </div>
      </header>

      <section className="mx-auto max-w-4xl px-6 py-10">
        <div className="mb-8 flex items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold">Listas</h1>

          <div className="flex gap-3">
            {currentUser?.role === "admin" && (
              <button
                onClick={() => setShowSeedForm((v) => !v)}
                className="rounded-full border border-gray-300 px-5 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50"
              >
                Generar automática
              </button>
            )}

            {currentUser && (
              <Link
                href="/lists/new"
                className="rounded-full bg-gray-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-gray-700"
              >
                Nueva lista
              </Link>
            )}
          </div>
        </div>

        {showSeedForm && (
          <form
            onSubmit={handleSeedSubmit}
            className="mb-8 space-y-3 rounded-lg border border-gray-200 p-5"
          >
            <h3 className="text-sm font-semibold text-gray-700">
              Generar lista automática
            </h3>

            <input
              value={seedTopic}
              onChange={(e) => setSeedTopic(e.target.value)}
              placeholder="Tema, ej: herramientas de ia"
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm outline-none focus:border-gray-500"
            />

            <select
              value={seedCategory}
              onChange={(e) => setSeedCategory(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm outline-none focus:border-gray-500"
            >
              <option value="">Generar automáticamente</option>
              {categories.map((cat) => (
                <optgroup key={cat.id} label={cat.name}>
                  <option value={cat.name}>{cat.name}</option>
                  {(cat.children ?? []).map((sub) => (
                    <option key={sub.id} value={sub.name}>
                      {"  "}↳ {sub.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>

            <div>
              <label className="mb-1 block text-xs text-gray-500">
                Número de enlaces a generar
              </label>
              <input
                type="number"
                min={1}
                max={20}
                value={seedMaxResults}
                onChange={(e) => setSeedMaxResults(Number(e.target.value))}
                className="w-24 rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-gray-500"
              />
            </div>

            {seedError && (
              <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
                {seedError}
              </p>
            )}

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={seedLoading}
                className="rounded-full bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-700 disabled:opacity-50"
              >
                {seedLoading ? "Generando..." : "Generar lista"}
              </button>

              <button
                type="button"
                onClick={() => setShowSeedForm(false)}
                className="rounded-full border border-gray-300 px-4 py-2 text-sm text-gray-700 transition hover:bg-gray-50"
              >
                Cancelar
              </button>
            </div>
          </form>
        )}

        {loading && <p className="text-sm text-gray-500">Cargando...</p>}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            No se pudieron cargar las listas.
          </div>
        )}

        {!loading && !error && lists.length === 0 && (
          <p className="text-sm text-gray-500">
            Todavía no hay listas creadas.
          </p>
        )}

        {!loading && !error && lists.length > 0 && (
          <div className="space-y-6">
            {lists.map((list) => (
              <article
                key={list.id}
                className="rounded-lg border border-gray-200 p-5 transition hover:border-gray-300"
              >
                <Link href={`/lists/${list.slug}`}>
                  <h2 className="mb-1 text-lg font-medium text-blue-700 hover:underline">
                    {list.title}
                  </h2>
                </Link>

                {list.description && (
                  <p className="mb-3 text-sm text-gray-600">
                    {list.description}
                  </p>
                )}

                <div className="flex items-center gap-4 text-xs text-gray-400">
                  <span>{list.points} puntos</span>
                  <span>
                    {new Date(list.created_at).toLocaleDateString("es-ES")}
                  </span>
                  <span>
                    por{" "}
                    <Link
                      href={`/users/${list.user_id}`}
                      className="text-blue-700 hover:underline"
                    >
                      {list.username ?? `usuario #${list.user_id}`}
                    </Link>
                  </span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
