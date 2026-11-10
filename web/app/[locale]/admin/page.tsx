"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/app/components/Navbar";
import { api, getToken, ApiRequestError } from "@/app/lib/api";
import { useLang } from "@/app/lib/lang";
import { format, DATE_LOCALES } from "@/app/lib/i18n";
import { AdminInvitation, Category } from "@/app/lib/types";

type CurrentUser = {
  id: number;
  username: string;
  email: string;
  role: string;
};

type InvitationFilter = "pending" | "all";

function statusBadgeClass(status: string): string {
  if (status === "approved") {
    return "rounded-full bg-green-50 px-2.5 py-1 text-xs text-green-700";
  }
  if (status === "rejected") {
    return "rounded-full bg-red-50 px-2.5 py-1 text-xs text-red-700";
  }
  return "rounded-full bg-yellow-50 px-2.5 py-1 text-xs text-yellow-700";
}

function CategoryRow({
  category,
  deleting,
  deleteLabel,
  onDelete,
}: {
  category: Category;
  deleting: boolean;
  deleteLabel: string;
  onDelete: (category: Category) => void;
}) {
  return (
    <div className="flex items-center justify-between px-4 py-3">
      <div>
        <p className="text-sm font-medium text-gray-900">{category.name}</p>
        <p className="text-xs text-gray-400">/{category.slug}</p>
      </div>

      <button
        type="button"
        disabled={deleting}
        onClick={() => onDelete(category)}
        className="rounded-full border border-red-300 px-4 py-1.5 text-sm text-red-600 transition hover:bg-red-50 disabled:opacity-50"
      >
        {deleteLabel}
      </button>
    </div>
  );
}

export default function AdminPage() {
  const router = useRouter();
  const { t, locale, path } = useLang();

  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [filter, setFilter] = useState<InvitationFilter>("pending");
  const [invitations, setInvitations] = useState<AdminInvitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actingId, setActingId] = useState<number | null>(null);

  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryName, setCategoryName] = useState("");
  const [savingCategory, setSavingCategory] = useState(false);
  const [deletingCategoryId, setDeletingCategoryId] = useState<number | null>(
    null
  );
  const [categoryError, setCategoryError] = useState<string | null>(null);
  const [categoryNotice, setCategoryNotice] = useState<string | null>(null);

  function statusLabel(status: string): string {
    if (status === "approved") {
      return t.profile.statusApproved;
    }
    if (status === "rejected") {
      return t.profile.statusRejected;
    }
    return t.profile.statusPending;
  }

  useEffect(() => {
    if (!getToken()) {
      router.push(path("/login"));
      return;
    }

    async function load() {
      try {
        const me = await api.get<CurrentUser>("/auth/me");

        if (me.role !== "admin") {
          setAllowed(false);
          setLoading(false);
          return;
        }

        setAllowed(true);
      } catch {
        setError(t.admin.errorAccount);
        setLoading(false);
      }
    }

    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router, locale]);

  useEffect(() => {
    if (allowed !== true) {
      return;
    }

    async function loadInvitations() {
      setLoading(true);
      setError(null);

      try {
        const query =
          filter === "pending" ? "?status=pending" : "";
        const data = await api.get<AdminInvitation[]>(
          `/admin/invitations${query}`
        );
        setInvitations(data);
      } catch (err) {
        if (err instanceof ApiRequestError) {
          setError(err.message);
        } else {
          setError(t.admin.errorInvitations);
        }
      } finally {
        setLoading(false);
      }
    }

    loadInvitations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allowed, filter, locale]);

  async function handleReview(invitationId: number, action: "approve" | "reject") {
    setActingId(invitationId);
    setError(null);

    try {
      await api.post(`/admin/invitations/${invitationId}/${action}`);

      setInvitations((prev) =>
        filter === "pending"
          ? prev.filter((inv) => inv.id !== invitationId)
          : prev.map((inv) =>
              inv.id === invitationId
                ? { ...inv, status: action === "approve" ? "approved" : "rejected" }
                : inv
            )
      );
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message);
      } else {
        setError(t.admin.errorProcess);
      }
    } finally {
      setActingId(null);
    }
  }

  useEffect(() => {
    if (allowed !== true) {
      return;
    }

    loadCategories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allowed, locale]);

  async function loadCategories() {
    try {
      const data = await api.get<Category[]>("/categories", { lang: locale });
      setCategories(data);
    } catch {
      setCategoryError(t.categories.errorLoad);
    }
  }

  async function handleCreateCategory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCategoryError(null);
    setCategoryNotice(null);

    const name = categoryName.trim();

    if (!name) {
      setCategoryError(t.admin.errorName);
      return;
    }

    setSavingCategory(true);

    try {
      const created = await api.post<Category>("/categories", {
        name,
      });

      setCategoryName("");
      setCategoryNotice(format(t.admin.createdNotice, { name: created.name }));
      await loadCategories();
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setCategoryError(err.message);
      } else {
        setCategoryError(t.admin.errorCreate);
      }
    } finally {
      setSavingCategory(false);
    }
  }

  async function handleDeleteCategory(category: Category) {
    const confirmText = format(t.admin.confirmDelete, { name: category.name });

    if (!window.confirm(confirmText)) {
      return;
    }

    setCategoryError(null);
    setCategoryNotice(null);
    setDeletingCategoryId(category.id);

    try {
      await api.delete(`/categories/${category.id}`);
      setCategoryNotice(format(t.admin.deletedNotice, { name: category.name }));
      await loadCategories();
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setCategoryError(err.message);
      } else {
        setCategoryError(t.admin.errorDelete);
      }
    } finally {
      setDeletingCategoryId(null);
    }
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

      <section className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold">{t.admin.title}</h1>
        <p className="mb-8 text-sm text-gray-500">
          {t.admin.intro}
        </p>

        {allowed === null && (
          <p className="text-sm text-gray-500">{t.common.loading}</p>
        )}

        {allowed === false && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {t.admin.noPermissions}
          </div>
        )}

        {allowed === true && (
          <>
            <div className="mb-4 flex gap-2">
              <button
                type="button"
                onClick={() => setFilter("pending")}
                className={`rounded-full border px-4 py-1.5 text-sm transition ${
                  filter === "pending"
                    ? "border-gray-900 bg-gray-900 text-white"
                    : "border-gray-300 text-gray-700 hover:border-gray-500"
                }`}
              >
                {t.admin.pendingFilter}
              </button>

              <button
                type="button"
                onClick={() => setFilter("all")}
                className={`rounded-full border px-4 py-1.5 text-sm transition ${
                  filter === "all"
                    ? "border-gray-900 bg-gray-900 text-white"
                    : "border-gray-300 text-gray-700 hover:border-gray-500"
                }`}
              >
                {t.admin.allFilter}
              </button>
            </div>

            {error && (
              <p className="mb-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
                {error}
              </p>
            )}

            {loading && <p className="text-sm text-gray-500">{t.common.loading}</p>}

            {!loading && invitations.length === 0 && (
              <p className="text-sm text-gray-500">
                {filter === "pending" ? t.admin.emptyPending : t.admin.emptyAll}
              </p>
            )}

            {!loading && invitations.length > 0 && (
              <div className="divide-y divide-gray-100 rounded-lg border border-gray-200">
                {invitations.map((invitation) => (
                  <div
                    key={invitation.id}
                    className="flex items-center justify-between px-4 py-3"
                  >
                    <div>
                      <p className="text-sm text-gray-900">
                        {format(t.admin.invited, {
                          inviter:
                            invitation.inviter_username ??
                            format(t.common.userFallback, {
                              id: invitation.inviter_id,
                            }),
                          invited:
                            invitation.invited_username ??
                            format(t.common.userFallback, {
                              id: invitation.invited_user_id,
                            }),
                        })}
                      </p>
                      <p className="text-xs text-gray-400">
                        {new Date(invitation.created_at).toLocaleDateString(
                          DATE_LOCALES[locale]
                        )}{" "}
                        · {invitation.points} {t.common.points}
                      </p>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className={statusBadgeClass(invitation.status)}>
                        {statusLabel(invitation.status)}
                      </span>

                      {invitation.status === "pending" && (
                        <>
                          <button
                            type="button"
                            disabled={actingId === invitation.id}
                            onClick={() => handleReview(invitation.id, "approve")}
                            className="rounded-full bg-gray-900 px-4 py-1.5 text-sm font-medium text-white transition hover:bg-gray-700 disabled:opacity-50"
                          >
                            {t.admin.approve}
                          </button>

                          <button
                            type="button"
                            disabled={actingId === invitation.id}
                            onClick={() => handleReview(invitation.id, "reject")}
                            className="rounded-full border border-gray-300 px-4 py-1.5 text-sm text-gray-700 transition hover:bg-gray-50 disabled:opacity-50"
                          >
                            {t.admin.reject}
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <h2 className="mb-1 mt-12 text-lg font-semibold">
              {t.admin.categoriesTitle}
            </h2>
            <p className="mb-4 text-sm text-gray-500">
              {t.admin.categoriesIntro}
            </p>

            {categoryError && (
              <p className="mb-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
                {categoryError}
              </p>
            )}

            {categoryNotice && (
              <p className="mb-4 rounded-lg bg-green-50 px-4 py-2 text-sm text-green-700">
                {categoryNotice}
              </p>
            )}

            <form
              onSubmit={handleCreateCategory}
              className="mb-6 flex flex-wrap items-end gap-3"
            >
              <div className="min-w-[200px] flex-1">
                <label
                  htmlFor="category-name"
                  className="mb-1 block text-sm text-gray-600"
                >
                  {t.admin.name}
                </label>
                <input
                  id="category-name"
                  type="text"
                  value={categoryName}
                  onChange={(event) => setCategoryName(event.target.value)}
                  placeholder={t.admin.namePlaceholder}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={savingCategory || !categoryName.trim()}
                className="rounded-full bg-gray-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-gray-700 disabled:opacity-50"
              >
                {t.admin.createCategory}
              </button>
            </form>

            {categories.length === 0 && (
              <p className="text-sm text-gray-500">
                {t.admin.emptyCategories}
              </p>
            )}

            {categories.length > 0 && (
              <div className="divide-y divide-gray-100 rounded-lg border border-gray-200">
                {categories.map((category) => (
                  <CategoryRow
                    key={category.id}
                    category={category}
                    deleting={deletingCategoryId === category.id}
                    deleteLabel={t.admin.delete}
                    onDelete={handleDeleteCategory}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </section>
    </main>
  );
}
