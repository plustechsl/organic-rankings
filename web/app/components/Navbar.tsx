"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, clearToken, getToken, ApiRequestError } from "@/app/lib/api";
import { useLang } from "@/app/lib/lang";
import { LOCALES } from "@/app/lib/i18n";

type CurrentUser = {
  id: number;
  username: string;
  email: string;
  role: string;
};

function LanguageSwitcher() {
  const { locale, t } = useLang();

  function switchTo(next: string) {
    if (next === locale) {
      return;
    }

    document.cookie = `NEXT_LOCALE=${next}; path=/; max-age=31536000`;

    const { pathname, search } = window.location;
    const rest = pathname.replace(/^\/(es|en|ca)(?=\/|$)/, "");

    window.location.href = `/${next}${rest}${search}`;
  }

  return (
    <span
      className="flex items-center gap-1 text-xs text-gray-500"
      aria-label={t.nav.changeLanguage}
    >
      {LOCALES.map((code, index) => (
        <span key={code} className="flex items-center">
          {index > 0 && <span className="text-gray-300">|</span>}
          <button
            type="button"
            onClick={() => switchTo(code)}
            className={`px-1 uppercase transition ${
              code === locale
                ? "font-semibold text-gray-900"
                : "hover:text-gray-900"
            }`}
          >
            {code}
          </button>
        </span>
      ))}
    </span>
  );
}

export default function Navbar() {
  const { t, path } = useLang();

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
    window.location.href = path("/");
  }

  if (loading) {
    return <div className="h-5 w-20" />;
  }

  if (user) {
    return (
      <div className="flex items-center gap-4 text-sm">
        <Link
          href={path("/categories")}
          className="text-gray-600 transition hover:text-gray-900"
        >
          {t.nav.categories}
        </Link>
        <Link
          href={path("/users")}
          className="text-gray-600 transition hover:text-gray-900"
        >
          {t.nav.users}
        </Link>
        {user.role === "admin" && (
          <Link
            href={path("/admin")}
            className="text-gray-600 transition hover:text-gray-900"
          >
            {t.nav.admin}
          </Link>
        )}
        <Link
          href={path("/donate")}
          className="rounded-full bg-gray-900 px-4 py-2 font-medium text-white transition hover:bg-gray-700"
        >
          {t.nav.donations}
        </Link>
        <Link
          href={path("/profile")}
          className="text-gray-600 transition hover:text-gray-900"
        >
          {t.nav.hello}{" "}
          <span className="font-medium text-gray-900">{user.username}</span>
        </Link>
        <button
          onClick={handleLogout}
          className="text-gray-600 transition hover:text-gray-900"
        >
          {t.nav.logout}
        </button>
        <LanguageSwitcher />
      </div>
    );
  }

  return (
    <div className="flex items-center gap-4 text-sm">
      <Link
        href={path("/categories")}
        className="text-gray-600 transition hover:text-gray-900"
      >
        {t.nav.categories}
      </Link>
      <Link
        href={path("/users")}
        className="text-gray-600 transition hover:text-gray-900"
      >
        {t.nav.users}
      </Link>
      <Link
        href={path("/donate")}
        className="rounded-full bg-gray-900 px-4 py-2 font-medium text-white transition hover:bg-gray-700"
      >
        {t.nav.donations}
      </Link>
      <Link
        href={path("/login")}
        className="text-gray-600 transition hover:text-gray-900"
      >
        {t.nav.login}
      </Link>
      <LanguageSwitcher />
    </div>
  );
}
