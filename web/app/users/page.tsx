"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Navbar from "@/app/components/Navbar";
import Avatar from "@/app/components/Avatar";
import { api } from "@/app/lib/api";
import { PublicUser } from "@/app/lib/types";

export default function UsersPage() {
  const [users, setUsers] = useState<PublicUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    api
      .get<PublicUser[]>("/users")
      .then(setUsers)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

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
        <h1 className="mb-2 text-2xl font-semibold">Usuarios</h1>
        <p className="mb-8 text-sm text-gray-500">
          Ordenados por aura: la valoración de los enlaces de sus listas más los puntos por invitaciones aprobadas.
        </p>

        {loading && <p className="text-sm text-gray-500">Cargando...</p>}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            No se pudieron cargar los usuarios.
          </div>
        )}

        {!loading && !error && users.length === 0 && (
          <p className="text-sm text-gray-500">
            Todavía no hay usuarios.
          </p>
        )}

        {!loading && !error && users.length > 0 && (
          <div className="space-y-3">
            {users.map((user, index) => (
              <Link
                key={user.id}
                href={`/users/${user.id}`}
                className="flex items-center gap-4 rounded-lg border border-gray-200 px-4 py-3 transition hover:border-gray-400"
              >
                <span className="w-6 text-sm text-gray-400">{index + 1}</span>
                <Avatar username={user.username} size="sm" />
                <span className="flex-1 font-medium text-blue-700">
                  {user.username}
                </span>
                <span className="text-sm font-medium text-gray-600">
                  {user.aura} aura
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
