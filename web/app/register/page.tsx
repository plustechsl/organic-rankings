"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken, ApiRequestError } from "@/app/lib/api";
import { Category } from "@/app/lib/types";
import Turnstile from "@/app/components/Turnstile";

type RegisterResponse = {
  id: number;
  username: string;
  email: string;
  role: string;
  access_token: string;
  token_type: string;
};

const MAX_EXPERTISES = 3;

export default function RegisterPage() {
  const router = useRouter();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategoryIds, setSelectedCategoryIds] = useState<number[]>([]);
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const turnstileSiteKey = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY;

  useEffect(() => {
    api
      .get<Category[]>("/categories")
      .then(setCategories)
      .catch(() => {});
  }, []);

  function toggleCategory(categoryId: number) {
    setSelectedCategoryIds((prev) => {
      if (prev.includes(categoryId)) {
        return prev.filter((id) => id !== categoryId);
      }
      if (prev.length >= MAX_EXPERTISES) {
        return prev;
      }
      return [...prev, categoryId];
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const registerData = await api.post<RegisterResponse>("/auth/register", {
        username,
        email,
        password,
        turnstile_token: turnstileToken,
      });

      setToken(registerData.access_token);

      for (const categoryId of selectedCategoryIds) {
        try {
          await api.post("/me/expertise", { category_id: categoryId });
        } catch {
          // si falla una especialidad concreta, seguimos con el resto
        }
      }

      router.push("/profile");
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message);
      } else {
        setError("No se pudo completar el registro.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-white px-6 py-12 text-gray-900">
      <div className="w-full max-w-md">
        <Link
          href="/"
          className="mb-8 block text-center text-xl font-semibold tracking-tight"
        >
          Organic Rankings
        </Link>

        <h1 className="mb-6 text-center text-2xl font-semibold">
          Crear cuenta
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="mb-1 block text-sm text-gray-600">
              Usuario
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 outline-none focus:border-gray-500"
            />
          </div>

          <div>
            <label htmlFor="email" className="mb-1 block text-sm text-gray-600">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 outline-none focus:border-gray-500"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1 block text-sm text-gray-600">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 outline-none focus:border-gray-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm text-gray-600">
              Tus especialidades (elige hasta {MAX_EXPERTISES}) —{" "}
              {selectedCategoryIds.length}/{MAX_EXPERTISES}
            </label>

            <div className="flex flex-wrap gap-2">
              {categories.map((cat) => {
                const isSelected = selectedCategoryIds.includes(cat.id);
                const isDisabled =
                  !isSelected && selectedCategoryIds.length >= MAX_EXPERTISES;

                return (
                  <button
                    key={cat.id}
                    type="button"
                    disabled={isDisabled}
                    onClick={() => toggleCategory(cat.id)}
                    className={`rounded-full border px-3 py-1.5 text-sm transition ${
                      isSelected
                        ? "border-gray-900 bg-gray-900 text-white"
                        : isDisabled
                        ? "border-gray-200 text-gray-300"
                        : "border-gray-300 text-gray-700 hover:border-gray-500"
                    }`}
                  >
                    {cat.name}
                  </button>
                );
              })}
            </div>

            {categories.length === 0 && (
              <p className="text-xs text-gray-400">
                No hay categorías disponibles todavía.
              </p>
            )}
          </div>

          {turnstileSiteKey && (
            <Turnstile siteKey={turnstileSiteKey} onToken={setTurnstileToken} />
          )}

          {error && (
            <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || (!!turnstileSiteKey && !turnstileToken)}
            className="w-full rounded-full bg-gray-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-gray-700 disabled:opacity-50"
          >
            {loading ? "Creando cuenta..." : "Crear cuenta"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-500">
          ¿Ya tienes cuenta?{" "}
          <Link href="/login" className="text-gray-900 hover:underline">
            Inicia sesión
          </Link>
        </p>
      </div>
    </main>
  );
}
