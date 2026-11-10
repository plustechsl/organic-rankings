"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/app/components/Navbar";
import { api, getToken, ApiRequestError } from "@/app/lib/api";
import { useLang } from "@/app/lib/lang";
import { Category, LinkList } from "@/app/lib/types";

export default function NewListPage() {
  const router = useRouter();
  const { t, locale, path } = useLang();

  const [categories, setCategories] = useState<Category[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState<number | "">("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.push(path("/login"));
      return;
    }

    setCheckingAuth(false);

    api
      .get<Category[]>("/categories", { lang: locale })
      .then(setCategories)
      .catch(() => setError(t.newList.errorLoadCategories));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, locale]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!categoryId) {
      setError(t.newList.chooseCategoryError);
      return;
    }

    setLoading(true);

    try {
      const newList = await api.post<LinkList>("/lists", {
        title,
        description: description || undefined,
        category_id: categoryId,
      });

      router.push(path(`/lists/${newList.slug}`));
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message);
      } else {
        setError(t.newList.errorCreate);
      }
    } finally {
      setLoading(false);
    }
  }

  if (checkingAuth) {
    return null;
  }

  return (
    <main className="min-h-screen bg-white text-gray-900">
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-5">
          <Link href={path("/")} className="text-xl font-semibold tracking-tight">
            Organic Rankings
          </Link>

          <Navbar />
        </div>
      </header>

      <section className="mx-auto max-w-xl px-6 py-10">
        <h1 className="mb-6 text-2xl font-semibold">{t.newList.title}</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="title" className="mb-1 block text-sm text-gray-600">
              {t.newList.titleLabel}
            </label>
            <input
              id="title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder={t.newList.titlePlaceholder}
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 outline-none focus:border-gray-500"
            />
          </div>

          <div>
            <label htmlFor="description" className="mb-1 block text-sm text-gray-600">
              {t.newList.descLabel}
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 outline-none focus:border-gray-500"
            />
          </div>

          <div>
            <label htmlFor="category" className="mb-1 block text-sm text-gray-600">
              {t.newList.categoryLabel}
            </label>
            <select
              id="category"
              value={categoryId}
              onChange={(e) =>
                setCategoryId(e.target.value ? Number(e.target.value) : "")
              }
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 outline-none focus:border-gray-500"
            >
              <option value="">{t.newList.chooseCategory}</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-full bg-gray-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-gray-700 disabled:opacity-50"
          >
            {loading ? t.newList.creating : t.newList.create}
          </button>
        </form>
      </section>
    </main>
  );
}
