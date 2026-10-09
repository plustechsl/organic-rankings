"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Navbar from "@/app/components/Navbar";
import { api } from "@/app/lib/api";
import { SearchResponse, LinkList } from "@/app/lib/types";

function parseQuery(raw: string) {
  let text = raw;
  let tag: string | null = null;
  let category: string | null = null;

  const tagMatch = text.match(/#(\S+)/);
  if (tagMatch) {
    tag = tagMatch[1];
    text = text.replace(tagMatch[0], "").trim();
  }

  const categoryMatch = text.match(/categoria:(\S+)/i);
  if (categoryMatch) {
    category = categoryMatch[1].replace(/-/g, " ");
    text = text.replace(categoryMatch[0], "").trim();
  }

  return { text: text.trim(), tag, category };
}

type FoundList = LinkList & { matchCount: number };

export default function SearchClient() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const rawQuery = searchParams.get("q") ?? "";

  const [inputValue, setInputValue] = useState(rawQuery);
  const [data, setData] = useState<SearchResponse | null>(null);
  const [foundLists, setFoundLists] = useState<FoundList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setInputValue(rawQuery);

    async function fetchResults() {
      setLoading(true);
      setError(false);

      const { text, tag, category } = parseQuery(rawQuery);

      const params = new URLSearchParams();

      if (text) params.set("q", text);
      if (tag) params.set("tag", tag);
      if (category) params.set("category", category);

      try {
        const result = await api.get<SearchResponse>(
          `/search?${params.toString()}`
        );

        setData(result);

        const listIdCounts = new Map<number, number>();

        for (const r of result.results) {
          listIdCounts.set(
            r.list_id,
            (listIdCounts.get(r.list_id) ?? 0) + 1
          );
        }

        if (listIdCounts.size > 0) {
          const allLists = await api.get<LinkList[]>("/lists");

          const matched = allLists
            .filter((l) => listIdCounts.has(l.id))
            .map((l) => ({
              ...l,
              matchCount: listIdCounts.get(l.id) ?? 0,
            }))
            .sort((a, b) => b.points - a.points);

          setFoundLists(matched);
        } else {
          setFoundLists([]);
        }
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    }

    fetchResults();
  }, [rawQuery]);

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    router.push(`/search?q=${encodeURIComponent(inputValue.trim())}`);
  }

  return (
    <main className="min-h-screen bg-white text-gray-900">
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-6xl items-center gap-8 px-6 py-5">
          <Link href="/" className="text-xl font-semibold tracking-tight">
            Organic Rankings
          </Link>

          <form
            onSubmit={handleSearch}
            className="flex max-w-2xl flex-1 items-center rounded-full border border-gray-300 px-4 py-1.5"
          >
            <span className="mr-3 text-lg text-gray-400">⌕</span>

            <input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Buscar... prueba #python o categoria:Tecnología"
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

      <section className="mx-auto max-w-4xl px-6 py-8">
        {rawQuery && (
          <p className="mb-8 text-sm text-gray-500">
            Resultados para &quot;{rawQuery}&quot;
          </p>
        )}

        {loading && <p className="text-sm text-gray-500">Buscando...</p>}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            No se pudo conectar con el buscador.
          </div>
        )}

        {!loading && !error && data && data.total === 0 && (
          <div className="py-10 text-center">
            <p className="text-lg font-medium">No encontramos resultados</p>
            <p className="mt-2 text-sm text-gray-500">
              Prueba con otra búsqueda.
            </p>
          </div>
        )}

        {!loading && !error && foundLists.length > 0 && (
          <div className="mb-10">
            <h2 className="mb-4 text-lg font-semibold">Listas encontradas</h2>

            <div className="space-y-3">
              {foundLists.map((list) => (
                <Link
                  key={list.id}
                  href={`/lists/${list.slug}`}
                  className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3 transition hover:border-gray-400"
                >
                  <div>
                    <p className="font-medium text-blue-700">{list.title}</p>
                    <p className="text-xs text-gray-400">
                      {list.matchCount}{" "}
                      {list.matchCount === 1
                        ? "enlace coincide"
                        : "enlaces coinciden"}
                    </p>
                  </div>

                  <span className="flex-shrink-0 text-sm font-medium text-gray-600">
                    {list.points} pts
                  </span>
                </Link>
              ))}
            </div>
          </div>
        )}

        {!loading && !error && data && data.total > 0 && (
          <div>
            <h2 className="mb-4 text-lg font-semibold">Enlaces</h2>

            <div className="space-y-8">
              {data.results.map((result) => (
                <article key={result.id}>
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group"
                  >
                    <p className="mb-1 text-sm text-green-700">
                      {result.url}
                    </p>

                    <h3 className="mb-2 text-xl font-medium text-blue-700 group-hover:underline">
                      {result.title}
                    </h3>

                    <p className="text-sm leading-6 text-gray-600">
                      {result.description}
                    </p>
                  </a>

                  <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-400">
                    <span>{result.points} puntos</span>

                    {result.category_name && (
                      <span>en {result.category_name}</span>
                    )}

                    {result.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-full bg-gray-100 px-2 py-0.5"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
