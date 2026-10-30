"use client";

import Link from "next/link";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/app/components/Navbar";
import Logo from "@/app/components/Logo";
import AdSlot from "@/app/components/AdSlot";
import { api, getToken, ApiRequestError } from "@/app/lib/api";
import { LinkList, Link as LinkType, Tag } from "@/app/lib/types";

type LinkWithTags = LinkType & { tags: Tag[] };

type VoteResponse = {
  link_id: number;
  points_awarded: number;
  link_total_points: number;
};

type CurrentUser = {
  id: number;
  username: string;
  email: string;
  role: string;
};

export default function ListDetailPage() {
  const params = useParams<{ slug: string }>();
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");

  const [list, setList] = useState<LinkList | null>(null);
  const [links, setLinks] = useState<LinkWithTags[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [voteMessage, setVoteMessage] = useState<string | null>(null);
  const [myVotedLinkIds, setMyVotedLinkIds] = useState<Set<number>>(new Set());
  const [adTheme, setAdTheme] = useState<string | null>(null);

  const [showNewLinkForm, setShowNewLinkForm] = useState(false);
  const [newLinkTitle, setNewLinkTitle] = useState("");
  const [newLinkUrl, setNewLinkUrl] = useState("");
  const [newLinkDescription, setNewLinkDescription] = useState("");
  const [newLinkError, setNewLinkError] = useState<string | null>(null);
  const [savingLink, setSavingLink] = useState(false);

  const [adminUsers, setAdminUsers] = useState<
    { id: number; username: string; is_active: boolean }[]
  >([]);
  const [newOwnerId, setNewOwnerId] = useState<number | null>(null);
  const [transferMessage, setTransferMessage] = useState<string | null>(null);
  const [transferring, setTransferring] = useState(false);

  const [tagInputs, setTagInputs] = useState<Record<number, string>>({});
  const [tagErrors, setTagErrors] = useState<Record<number, string>>({});

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const allLists = await api.get<LinkList[]>("/lists");
      const found = allLists.find((l) => l.slug === params.slug);

      if (!found) {
        setError("Lista no encontrada.");
        setLoading(false);
        return;
      }

      setList(found);
      setNewOwnerId(found.user_id);

      if (found.category_id) {
        try {
          const categories = await api.get<any[]>("/categories");
          const cat = categories.find((c) => c.id === found.category_id);
          if (cat?.slug) setAdTheme(cat.slug);
          else if (cat?.name) setAdTheme(cat.name.replace(/\s+/g, "-").toLowerCase());
        } catch {
          // ignore
        }
      }

      const listLinks = await api.get<LinkType[]>(
        `/links?list_id=${found.id}`
      );

      const linksWithTags = await Promise.all(
        listLinks.map(async (link) => {
          try {
            const tags = await api.get<Tag[]>(`/links/${link.id}/tags`);
            return { ...link, tags };
          } catch {
            return { ...link, tags: [] };
          }
        })
      );

      setLinks(linksWithTags);
    } catch {
      setError("No se pudo cargar la lista.");
    } finally {
      setLoading(false);
    }
  }, [params.slug]);

  useEffect(() => {
    if (getToken()) {
      api
        .get<CurrentUser>("/auth/me")
        .then(setCurrentUser)
        .catch(() => setCurrentUser(null));

      api
        .get<{ link_id: number; points: number }[]>("/me/votes")
        .then((votes) => setMyVotedLinkIds(new Set(votes.map((v) => v.link_id))))
        .catch(() => {});
    }

    loadData();
  }, [loadData]);

  useEffect(() => {
    if (currentUser?.role !== "admin") return;

    api
      .get<{ id: number; username: string; is_active: boolean }[]>("/admin/users")
      .then((users) => setAdminUsers(users.filter((u) => u.is_active)))
      .catch(() => setAdminUsers([]));
  }, [currentUser]);

  function canManageLink(link: LinkWithTags): boolean {
    if (!currentUser) return false;
    return (
      currentUser.id === link.user_id ||
      currentUser.role === "admin" ||
      currentUser.role === "moderator"
    );
  }

  async function handleVote(linkId: number) {
    if (!currentUser) {
      router.push("/login");
      return;
    }

    setVoteMessage(null);

    const alreadyVoted = myVotedLinkIds.has(linkId);

    try {
      if (alreadyVoted) {
        const result = await api.delete<{ link_id: number; link_total_points: number }>(
          `/links/${linkId}/vote`
        );

        setVoteMessage("Has quitado tu voto.");

        setLinks((prev) =>
          prev.map((l) =>
            l.id === linkId ? { ...l, points: result.link_total_points } : l
          )
        );

        setMyVotedLinkIds((prev) => {
          const next = new Set(prev);
          next.delete(linkId);
          return next;
        });
      } else {
        const result = await api.post<VoteResponse>(`/links/${linkId}/vote`);

        setVoteMessage(`¡Voto registrado! (+${result.points_awarded} puntos)`);

        setLinks((prev) =>
          prev.map((l) =>
            l.id === linkId ? { ...l, points: result.link_total_points } : l
          )
        );

        setMyVotedLinkIds((prev) => new Set(prev).add(linkId));
      }
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setVoteMessage(err.message);
      } else {
        setVoteMessage("No se pudo actualizar el voto.");
      }
    }
  }

  async function handleCreateLink(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNewLinkError(null);

    if (!list) return;

    setSavingLink(true);

    try {
      const newLink = await api.post<LinkType>("/links", {
        list_id: list.id,
        title: newLinkTitle,
        url: newLinkUrl,
        description: newLinkDescription || undefined,
      });

      setLinks((prev) => [...prev, { ...newLink, tags: [] }]);
      setNewLinkTitle("");
      setNewLinkUrl("");
      setNewLinkDescription("");
      setShowNewLinkForm(false);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setNewLinkError(err.message);
      } else {
        setNewLinkError("No se pudo crear el enlace.");
      }
    } finally {
      setSavingLink(false);
    }
  }

  async function handleAddTags(linkId: number) {
    const raw = tagInputs[linkId] ?? "";
    const tags = raw
      .split(/[\s,]+/)
      .map((t) => t.replace(/^#/, "").trim())
      .filter(Boolean);

    if (tags.length === 0) return;

    setTagErrors((prev) => ({ ...prev, [linkId]: "" }));

    try {
      const updatedTags = await api.post<Tag[]>(`/links/${linkId}/tags`, {
        tags,
      });

      setLinks((prev) =>
        prev.map((l) => (l.id === linkId ? { ...l, tags: updatedTags } : l))
      );
      setTagInputs((prev) => ({ ...prev, [linkId]: "" }));
    } catch (err) {
      const message =
        err instanceof ApiRequestError
          ? err.message
          : "No se pudieron añadir los tags.";
      setTagErrors((prev) => ({ ...prev, [linkId]: message }));
    }
  }

  async function handleRemoveTag(linkId: number, tagId: number) {
    try {
      await api.delete(`/links/${linkId}/tags/${tagId}`);

      setLinks((prev) =>
        prev.map((l) =>
          l.id === linkId
            ? { ...l, tags: l.tags.filter((t) => t.id !== tagId) }
            : l
        )
      );
    } catch {
      // silently ignore, tag stays visible
    }
  }

  async function handleTransferList() {
    if (!list || !newOwnerId) return;

    setTransferring(true);
    setTransferMessage(null);

    try {
      await api.patch(`/admin/lists/${list.id}/owner?user_id=${newOwnerId}`);

      setTransferMessage("Propietario actualizado.");

      await loadData();
    } catch (err) {
      setTransferMessage(
        err instanceof ApiRequestError
          ? err.message
          : "No se pudo cambiar el propietario."
      );
    } finally {
      setTransferring(false);
    }
  }

  function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmed = searchQuery.trim();

    if (!trimmed) {
      return;
    }

    router.push(`/search?q=${encodeURIComponent(trimmed)}`);
  }

  return (
    <main className="min-h-screen bg-white text-gray-900">
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-6xl items-center gap-8 px-6 py-5">
          <Link
            href="/"
            className="flex flex-shrink-0 items-center gap-2 text-xl font-semibold tracking-tight"
          >
            <Logo className="h-6 w-6" />
            Organic Rankings
          </Link>

          <form
            onSubmit={handleSearch}
            className="flex max-w-2xl flex-1 items-center rounded-full border border-gray-300 px-4 py-1.5"
          >
            <span className="mr-3 text-lg text-gray-400">⌕</span>

            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar listas y enlaces..."
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

      <section className="mx-auto max-w-6xl px-6 py-10">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-[250px_1fr_250px]">
          <aside className="hidden lg:block">
            <div className="sticky top-8">
              <AdSlot themeSlug={adTheme} />
            </div>
          </aside>

          <div>
            <Link
              href="/lists"
              className="mb-6 inline-block text-sm text-gray-500 hover:text-gray-900"
            >
              ← Volver a listas
            </Link>

            {loading && <p className="text-sm text-gray-500">Cargando...</p>}

            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                {error}
              </div>
            )}

            {!loading && !error && list && (
              <>
                <div className="mb-2 flex items-start justify-between">
                  <h1 className="text-3xl font-semibold">{list.title}</h1>

                  {currentUser && !showNewLinkForm && (
                    <button
                      onClick={() => setShowNewLinkForm(true)}
                      className="flex-shrink-0 rounded-full bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-700"
                    >
                      Añadir enlace
                    </button>
                  )}
                </div>

                {list.description && (
                  <p className="mb-4 text-gray-600">{list.description}</p>
                )}

                <div className="mb-8 flex items-center gap-4 text-xs text-gray-400">
                  <span>{list.points} puntos</span>
                  <span>
                    {new Date(list.created_at).toLocaleDateString("es-ES")}
                  </span>
                  <span>
                    por{" "}
                    <Link
                      href={`/users/${list.user_id}`}
                      className="text-blue-700 hover:underline"
                    >
                      {list.username ?? `usuario #${list.user_id}`}
                    </Link>
                  </span>
                </div>

                {currentUser?.role === "admin" && (
                  <div className="mb-8 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                    <span>Propietario:</span>

                    <select
                      value={newOwnerId ?? list.user_id}
                      onChange={(e) => setNewOwnerId(Number(e.target.value))}
                      className="rounded-lg border border-gray-300 px-2 py-1 text-xs outline-none focus:border-gray-500"
                    >
                      {!adminUsers.some((u) => u.id === list.user_id) && (
                        <option value={list.user_id}>
                          {list.username ?? `usuario #${list.user_id}`}
                        </option>
                      )}

                      {adminUsers.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.username}
                        </option>
                      ))}
                    </select>

                    <button
                      onClick={handleTransferList}
                      disabled={transferring || newOwnerId === list.user_id}
                      className="rounded-full border border-gray-300 px-3 py-1 text-xs text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                    >
                      {transferring ? "Cambiando..." : "Cambiar"}
                    </button>

                    {transferMessage && <span>{transferMessage}</span>}
                  </div>
                )}

                {showNewLinkForm && (
                  <form
                    onSubmit={handleCreateLink}
                    className="mb-8 space-y-3 rounded-lg border border-gray-200 p-5"
                  >
                    <h3 className="text-sm font-semibold text-gray-700">
                      Nuevo enlace
                    </h3>

                    <input
                      value={newLinkTitle}
                      onChange={(e) => setNewLinkTitle(e.target.value)}
                      placeholder="Título"
                      required
                      className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm outline-none focus:border-gray-500"
                    />

                    <input
                      value={newLinkUrl}
                      onChange={(e) => setNewLinkUrl(e.target.value)}
                      placeholder="https://..."
                      required
                      className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm outline-none focus:border-gray-500"
                    />

                    <textarea
                      value={newLinkDescription}
                      onChange={(e) => setNewLinkDescription(e.target.value)}
                      placeholder="Descripción (opcional)"
                      rows={2}
                      className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm outline-none focus:border-gray-500"
                    />

                    {newLinkError && (
                      <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
                        {newLinkError}
                      </p>
                    )}

                    <div className="flex gap-3">
                      <button
                        type="submit"
                        disabled={savingLink}
                        className="rounded-full bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-700 disabled:opacity-50"
                      >
                        {savingLink ? "Guardando..." : "Guardar enlace"}
                      </button>

                      <button
                        type="button"
                        onClick={() => setShowNewLinkForm(false)}
                        className="rounded-full border border-gray-300 px-4 py-2 text-sm text-gray-700 transition hover:bg-gray-50"
                      >
                        Cancelar
                      </button>
                    </div>
                  </form>
                )}

                {voteMessage && (
                  <div className="mb-6 rounded-lg bg-gray-50 px-4 py-2 text-sm text-gray-700">
                    {voteMessage}
                  </div>
                )}

                {links.length === 0 && (
                  <p className="text-sm text-gray-500">
                    Esta lista todavía no tiene enlaces.
                  </p>
                )}

                <div className="space-y-5">
                  {links.map((link) => (
                    <article
                      key={link.id}
                      className="rounded-lg border border-gray-200 p-5"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-baseline gap-x-2">
                            <a
                              href={link.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-lg font-medium text-blue-700 hover:underline"
                            >
                              {link.title}
                            </a>

                            {link.username && (
                              <Link
                                href={`/users/${link.user_id}`}
                                className="text-xs text-gray-400 hover:underline"
                              >
                                por {link.username}
                              </Link>
                            )}
                          </div>

                          <p className="mt-1 truncate text-sm text-green-700">
                            {link.url}
                          </p>

                          {link.description && (
                            <p className="mt-2 text-sm text-gray-600">
                              {link.description}
                            </p>
                          )}

                          {link.tags.length > 0 && (
                            <div className="mt-3 flex flex-wrap gap-2">
                              {link.tags.map((tag) => (
                                <span
                                  key={tag.id}
                                  className="flex items-center gap-1 rounded-full bg-gray-100 px-3 py-1 text-xs text-gray-600"
                                >
                                  #{tag.slug}
                                  {canManageLink(link) && (
                                    <button
                                      onClick={() =>
                                        handleRemoveTag(link.id, tag.id)
                                      }
                                      className="text-gray-400 hover:text-gray-700"
                                      aria-label={`Quitar tag ${tag.name}`}
                                    >
                                      ×
                                    </button>
                                  )}
                                </span>
                              ))}
                            </div>
                          )}

                          {canManageLink(link) && link.tags.length < 10 && (
                            <div className="mt-3 flex items-center gap-2">
                              <input
                                value={tagInputs[link.id] ?? ""}
                                onChange={(e) =>
                                  setTagInputs((prev) => ({
                                    ...prev,
                                    [link.id]: e.target.value,
                                  }))
                                }
                                onKeyDown={(e) => {
                                  if (e.key === "Enter") {
                                    e.preventDefault();
                                    handleAddTags(link.id);
                                  }
                                }}
                                placeholder="Añadir tags (separados por espacio)"
                                className="flex-1 rounded-full border border-gray-300 px-3 py-1 text-xs outline-none focus:border-gray-500"
                              />
                              <button
                                onClick={() => handleAddTags(link.id)}
                                className="rounded-full border border-gray-300 px-3 py-1 text-xs text-gray-700 hover:bg-gray-50"
                              >
                                Añadir
                              </button>
                            </div>
                          )}

                          {tagErrors[link.id] && (
                            <p className="mt-1 text-xs text-red-600">
                              {tagErrors[link.id]}
                            </p>
                          )}
                        </div>

                        <div className="flex flex-shrink-0 flex-col items-center gap-1">
                          <button
                            onClick={() => handleVote(link.id)}
                            title={
                              !currentUser
                                ? "Inicia sesión para votar"
                                : myVotedLinkIds.has(link.id)
                                ? "Quitar tu voto"
                                : "Votar este enlace"
                            }
                            className={`rounded-full border px-3 py-1.5 text-sm transition ${
                              myVotedLinkIds.has(link.id)
                                ? "border-gray-900 bg-gray-900 text-white"
                                : "border-gray-300 text-gray-700 hover:border-gray-500 hover:bg-gray-50"
                            }`}
                          >
                            ▲ {link.points}
                          </button>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </>
            )}

            <div className="mt-6 lg:hidden">
              <AdSlot themeSlug={adTheme} />
            </div>
          </div>

          <aside className="hidden lg:block">
            <div className="sticky top-8">
              <AdSlot themeSlug={adTheme} />
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
