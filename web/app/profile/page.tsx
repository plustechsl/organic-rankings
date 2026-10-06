"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/app/components/Navbar";
import Avatar from "@/app/components/Avatar";
import { api, getToken, ApiRequestError } from "@/app/lib/api";
import { LinkList, Category } from "@/app/lib/types";

type CurrentUser = {
  id: number;
  username: string;
  email: string;
  role: string;
};

export default function ProfilePage() {
  const router = useRouter();

  const [user, setUser] = useState<CurrentUser | null>(null);
  const [myLists, setMyLists] = useState<LinkList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const [editingProfile, setEditingProfile] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSuccess, setProfileSuccess] = useState<string | null>(null);
  const [savingProfile, setSavingProfile] = useState(false);

  const [editingPassword, setEditingPassword] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
  const [savingPassword, setSavingPassword] = useState(false);

  const [expertiseCategories, setExpertiseCategories] = useState<Category[]>([]);
  const [myExpertiseIds, setMyExpertiseIds] = useState<number[]>([]);
  const [expertiseError, setExpertiseError] = useState<string | null>(null);
  const [savingExpertise, setSavingExpertise] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }

    async function load() {
      try {
        const me = await api.get<CurrentUser>("/auth/me");
        setUser(me);
        setUsername(me.username);
        setEmail(me.email);

        const allLists = await api.get<LinkList[]>("/lists");
        setMyLists(allLists.filter((l) => l.user_id === me.id));
        const allCategories = await api.get<Category[]>("/categories");
        setExpertiseCategories(allCategories);

        const myExpertise = await api.get<{ category_id: number }[]>("/me/expertise");
        setMyExpertiseIds(myExpertise.map((e) => e.category_id));

      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [router]);

  async function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setProfileError(null);
    setProfileSuccess(null);
    setSavingProfile(true);

    try {
      const updated = await api.patch<CurrentUser>("/auth/me", {
        username,
        email,
      });

      setUser(updated);
      setProfileSuccess("Perfil actualizado correctamente.");
      setEditingProfile(false);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setProfileError(err.message);
      } else {
        setProfileError("No se pudo actualizar el perfil.");
      }
    } finally {
      setSavingProfile(false);
    }
  }

  async function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(null);
    setSavingPassword(true);

    try {
      await api.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });

      setPasswordSuccess("Contraseña actualizada correctamente.");
      setCurrentPassword("");
      setNewPassword("");
      setEditingPassword(false);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setPasswordError(err.message);
      } else {
        setPasswordError("No se pudo cambiar la contraseña.");
      }
    } finally {
      setSavingPassword(false);
    }
  }

  async function handleAddExpertise(categoryId: number) {
    setExpertiseError(null);
    setSavingExpertise(true);

    try {
      await api.post("/me/expertise", { category_id: categoryId });
      setMyExpertiseIds((prev) => [...prev, categoryId]);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setExpertiseError(err.message);
      } else {
        setExpertiseError("No se pudo añadir la especialidad.");
      }
    } finally {
      setSavingExpertise(false);
    }
  }

  async function handleRemoveExpertise(categoryId: number) {
    setExpertiseError(null);
    setSavingExpertise(true);

    try {
      await api.delete(`/me/expertise/${categoryId}`);
      setMyExpertiseIds((prev) => prev.filter((id) => id !== categoryId));
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setExpertiseError(err.message);
      } else {
        setExpertiseError("No se pudo quitar la especialidad.");
      }
    } finally {
      setSavingExpertise(false);
    }
  }
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
        {loading && <p className="text-sm text-gray-500">Cargando...</p>}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            No se pudo cargar tu perfil.
          </div>
        )}

        {!loading && !error && user && (
          <>
            <div className="mb-8 flex items-center gap-4">
              <Avatar username={user.username} size="lg" />

              <div>
                <h1 className="text-2xl font-semibold">{user.username}</h1>
                <p className="text-sm text-gray-500">
                  {user.email} · {user.role}
                </p>
              </div>
            </div>

            <div className="mb-8 rounded-lg border border-gray-200 p-5">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
                  Datos de la cuenta
                </h2>

                {!editingProfile && (
                  <button
                    onClick={() => {
                      setEditingProfile(true);
                      setProfileSuccess(null);
                    }}
                    className="text-sm text-blue-700 hover:underline"
                  >
                    Editar
                  </button>
                )}
              </div>

              {profileSuccess && !editingProfile && (
                <p className="mb-3 rounded-lg bg-green-50 px-4 py-2 text-sm text-green-700">
                  {profileSuccess}
                </p>
              )}

              {editingProfile ? (
                <form onSubmit={handleProfileSubmit} className="space-y-4">
                  <div>
                    <label className="mb-1 block text-sm text-gray-600">
                      Usuario
                    </label>
                    <input
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      required
                      className="w-full rounded-lg border border-gray-300 px-4 py-2.5 outline-none focus:border-gray-500"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm text-gray-600">
                      Email
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      className="w-full rounded-lg border border-gray-300 px-4 py-2.5 outline-none focus:border-gray-500"
                    />
                  </div>

                  {profileError && (
                    <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
                      {profileError}
                    </p>
                  )}

                  <div className="flex gap-3">
                    <button
                      type="submit"
                      disabled={savingProfile}
                      className="rounded-full bg-gray-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-gray-700 disabled:opacity-50"
                    >
                      {savingProfile ? "Guardando..." : "Guardar"}
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setEditingProfile(false);
                        setUsername(user.username);
                        setEmail(user.email);
                        setProfileError(null);
                      }}
                      className="rounded-full border border-gray-300 px-5 py-2 text-sm text-gray-700 transition hover:bg-gray-50"
                    >
                      Cancelar
                    </button>
                  </div>
                </form>
              ) : (
                <p className="text-sm text-gray-600">
                  Usuario: {user.username} · Email: {user.email}
                </p>
              )}
            </div>

            <div className="mb-8 rounded-lg border border-gray-200 p-5">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
                  Contraseña
                </h2>

                {!editingPassword && (
                  <button
                    onClick={() => {
                      setEditingPassword(true);
                      setPasswordSuccess(null);
                    }}
                    className="text-sm text-blue-700 hover:underline"
                  >
                    Cambiar contraseña
                  </button>
                )}
              </div>

              {passwordSuccess && !editingPassword && (
                <p className="mb-3 rounded-lg bg-green-50 px-4 py-2 text-sm text-green-700">
                  {passwordSuccess}
                </p>
              )}

              {editingPassword && (
                <form onSubmit={handlePasswordSubmit} className="space-y-4">
                  <div>
                    <label className="mb-1 block text-sm text-gray-600">
                      Contraseña actual
                    </label>
                    <input
                      type="password"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      required
                      className="w-full rounded-lg border border-gray-300 px-4 py-2.5 outline-none focus:border-gray-500"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm text-gray-600">
                      Nueva contraseña
                    </label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      required
                      minLength={8}
                      className="w-full rounded-lg border border-gray-300 px-4 py-2.5 outline-none focus:border-gray-500"
                    />
                    <p className="mt-1 text-xs text-gray-400">
                      Mínimo 8 caracteres.
                    </p>
                  </div>

                  {passwordError && (
                    <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
                      {passwordError}
                    </p>
                  )}

                  <div className="flex gap-3">
                    <button
                      type="submit"
                      disabled={savingPassword}
                      className="rounded-full bg-gray-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-gray-700 disabled:opacity-50"
                    >
                      {savingPassword ? "Guardando..." : "Guardar"}
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setEditingPassword(false);
                        setCurrentPassword("");
                        setNewPassword("");
                        setPasswordError(null);
                      }}
                      className="rounded-full border border-gray-300 px-5 py-2 text-sm text-gray-700 transition hover:bg-gray-50"
                    >
                      Cancelar
                    </button>
                  </div>
                </form>
              )}
            </div>

            <div className="mb-8 rounded-lg border border-gray-200 p-5">
              <h2 className="mb-1 text-sm font-semibold uppercase tracking-wide text-gray-500">
                Especialidades
              </h2>
              <p className="mb-4 text-xs text-gray-400">
                Elige hasta 3. Tus votos en listas de estas categorías valdrán más puntos.
              </p>

              <div className="flex flex-wrap gap-2">
                {expertiseCategories.map((cat) => {
                  const isSelected = myExpertiseIds.includes(cat.id);
                  const isDisabled =
                    !isSelected && myExpertiseIds.length >= 3;

                  return (
                    <button
                      key={cat.id}
                      type="button"
                      disabled={savingExpertise || isDisabled}
                      onClick={() =>
                        isSelected
                          ? handleRemoveExpertise(cat.id)
                          : handleAddExpertise(cat.id)
                      }
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

              {expertiseError && (
                <p className="mt-3 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
                  {expertiseError}
                </p>
              )}
            </div>

            <div className="mb-8 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Mis listas</h2>

              <Link
                href="/lists/new"
                className="rounded-full bg-gray-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-gray-700"
              >
                Nueva lista
              </Link>
            </div>

            {myLists.length === 0 && (
              <p className="text-sm text-gray-500">
                Todavía no has creado ninguna lista.
              </p>
            )}

            {myLists.length > 0 && (
              <div className="space-y-4">
                {myLists.map((list) => (
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
