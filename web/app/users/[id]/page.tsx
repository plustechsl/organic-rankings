"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Navbar from "@/app/components/Navbar";
import Avatar from "@/app/components/Avatar";
import { api, ApiRequestError } from "@/app/lib/api";
import { PublicUserProfile } from "@/app/lib/types";

export default function PublicProfilePage() {
  const params = useParams<{ id: string }>();

  const [profile, setProfile] = useState<PublicUserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.get<PublicUserProfile>(`/users/${params.id}`);
        setProfile(data);
      } catch (err) {
        if (err instanceof ApiRequestError && err.status === 404) {
          setNotFound(true);
        } else {
          setError(true);
        }
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [params.id]);

  return (
    <main className="min-h-screen bg-white text-gray-900">
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-5">
          <Link href="/" className="text-xl font-semibold tracking-tight">
            Organic Rankings
          </Link>

          <Navbar />
        </div>
      </header>

      <section className="mx-auto max-w-4xl px-6 py-10">
        <Link
          href="/users"
          className="mb-6 inline-block text-sm text-gray-500 hover:text-gray-900"
        >
          ← Usuarios
        </Link>

        {loading && <p className="text-sm text-gray-500">Cargando...</p>}

        {notFound && (
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
            Usuario no encontrado.
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            No se pudo cargar el perfil.
          </div>
        )}

        {!loading && !notFound && !error && profile && (
          <>
            <div className="mb-8 flex items-center gap-4">
              <Avatar username={profile.username} size="lg" />

              <div>
                <h1 className="text-2xl font-semibold">{profile.username}</h1>
                <p className="text-sm text-gray-500">
                  Miembro desde{" "}
                  {new Date(profile.created_at).toLocaleDateString("es-ES")}
                </p>
              </div>
            </div>

            <div className="mb-8 rounded-lg border border-gray-200 p-5">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
                Aura
              </h2>
              <p className="mt-2 text-3xl font-semibold">{profile.aura}</p>
              <p className="mt-1 text-xs text-gray-400">
                Suma de la valoración de los enlaces de sus listas.
              </p>
            </div>

            <h2 className="mb-4 text-lg font-semibold">
              Listas de {profile.username}
            </h2>

            {profile.lists.length === 0 && (
              <p className="text-sm text-gray-500">
                Todavía no ha creado ninguna lista.
              </p>
            )}

            {profile.lists.length > 0 && (
              <div className="space-y-4">
                {profile.lists.map((list) => (
                  <Link
                    key={list.id}
                    href={`/lists/${list.slug}`}
                    className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3 transition hover:border-gray-400"
                  >
                    <div>
                      <p className="font-medium text-blue-700">{list.title}</p>
                      <p className="text-xs text-gray-400">
                        {new Date(list.created_at).toLocaleDateString("es-ES")}
                      </p>
                    </div>

                    <span className="text-sm font-medium text-gray-600">
                      {list.points} pts
                    </span>
                  </Link>
                ))}
              </div>
            )}
          </>
        )}
      </section>
    </main>
  );
}
