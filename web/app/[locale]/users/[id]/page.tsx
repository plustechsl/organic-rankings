"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Navbar from "@/app/components/Navbar";
import Avatar from "@/app/components/Avatar";
import { api, ApiRequestError } from "@/app/lib/api";
import { useLang } from "@/app/lib/lang";
import { format, DATE_LOCALES } from "@/app/lib/i18n";
import { PublicUserProfile } from "@/app/lib/types";

export default function PublicProfilePage() {
  const params = useParams<{ id: string }>();
  const { t, locale, path } = useLang();

  const [profile, setProfile] = useState<PublicUserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.get<PublicUserProfile>(`/users/${params.id}`, {
          lang: locale,
        });
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
  }, [params.id, locale]);

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

      <section className="mx-auto max-w-4xl px-6 py-10">
        <Link
          href={path("/users")}
          className="mb-6 inline-block text-sm text-gray-500 hover:text-gray-900"
        >
          {t.userDetail.back}
        </Link>

        {loading && <p className="text-sm text-gray-500">{t.common.loading}</p>}

        {notFound && (
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
            {t.userDetail.notFound}
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {t.userDetail.errorLoad}
          </div>
        )}

        {!loading && !notFound && !error && profile && (
          <>
            <div className="mb-8 flex items-center gap-4">
              <Avatar username={profile.username} size="lg" />

              <div>
                <h1 className="text-2xl font-semibold">{profile.username}</h1>
                <p className="text-sm text-gray-500">
                  {format(t.userDetail.memberSince, {
                    date: new Date(profile.created_at).toLocaleDateString(
                      DATE_LOCALES[locale]
                    ),
                  })}
                </p>
              </div>
            </div>

            {profile.role !== "admin" && (
              <div className="mb-8 rounded-lg border border-gray-200 p-5">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
                  {t.userDetail.aura}
                </h2>
                <p className="mt-2 text-3xl font-semibold">{profile.aura}</p>
                <p className="mt-1 text-xs text-gray-400">
                  {t.userDetail.auraHint}
                </p>
              </div>
            )}

            <h2 className="mb-4 text-lg font-semibold">
              {format(t.userDetail.listsOf, { username: profile.username })}
            </h2>

            {profile.lists.length === 0 && (
              <p className="text-sm text-gray-500">
                {t.userDetail.emptyLists}
              </p>
            )}

            {profile.lists.length > 0 && (
              <div className="space-y-4">
                {profile.lists.map((list) => (
                  <Link
                    key={list.id}
                    href={path(`/lists/${list.slug}`)}
                    className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3 transition hover:border-gray-400"
                  >
                    <div>
                      <p className="font-medium text-blue-700">{list.title}</p>
                      <p className="text-xs text-gray-400">
                        {new Date(list.created_at).toLocaleDateString(
                          DATE_LOCALES[locale]
                        )}
                      </p>
                    </div>

                    <span className="text-sm font-medium text-gray-600">
                      {list.points} {t.common.pts}
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
