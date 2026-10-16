"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, clearToken, getToken, ApiRequestError } from "@/app/lib/api";

type CurrentUser = {
  id: number;
  username: string;
  email: string;
  role: string;
};

export default function Navbar() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      const token = getToken();

      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const me = await api.get<CurrentUser>("/auth/me");
        setUser(me);
      } catch (err) {
        if (err instanceof ApiRequestError && err.status === 401) {
          clearToken();
        }
      } finally {
        setLoading(false);
      }
    }

    loadUser();
  }, []);

  function handleLogout() {
    clearToken();
    window.location.href = "/";
  }

  if (loading) {
    return <div className="h-5 w-20" />;
  }

  if (user) {
    return (
      <div className="flex items-center gap-4 text-sm">
        <Link
          href="/users"
          className="text-gray-600 transition hover:text-gray-900"
        >
          Usuarios
        </Link>
        {user.role === "admin" && (
          <Link
            href="/admin"
            className="text-gray-600 transition hover:text-gray-900"
          >
            Admin
          </Link>
        )}
        <Link
          href="/donate"
          className="rounded-full bg-gray-900 px-4 py-2 font-medium text-white transition hover:bg-gray-700"
        >
          Donaciones
        </Link>
        <Link href="/profile" className="text-gray-600 transition hover:text-gray-900">
          Hola, <span className="font-medium text-gray-900">{user.username}</span>
        </Link>
        <button
          onClick={handleLogout}
          className="text-gray-600 transition hover:text-gray-900"
        >
          Cerrar sesión
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-4 text-sm">
      <Link
        href="/users"
        className="text-gray-600 transition hover:text-gray-900"
      >
        Usuarios
      </Link>
      <Link
        href="/donate"
        className="rounded-full bg-gray-900 px-4 py-2 font-medium text-white transition hover:bg-gray-700"
      >
        Donaciones
      </Link>
      <Link
        href="/login"
        className="text-gray-600 transition hover:text-gray-900"
      >
        Iniciar sesión
      </Link>
    </div>
  );
}
