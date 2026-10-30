"use client";

import Link from "next/link";
import AiBadge from "@/app/components/AiBadge";
import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/app/components/Navbar";
import Logo from "@/app/components/Logo";
import AdSlot from "@/app/components/AdSlot";
import SensitivityBadge from "@/app/components/SensitivityBadge";
import { api, getToken, ApiRequestError } from "@/app/lib/api";
import {
  LinkList,
  Link as LinkType,
  LinkPreview,
  LinkRequest,
  Sensitivity,
  Tag,
} from "@/app/lib/types";
import {
  SENSITIVITY_OPTIONS,
  confirmSensitiveOpen,
} from "@/app/lib/sensitivity";

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
  const [newLinkSensitivity, setNewLinkSensitivity] =
    useState<Sensitivity>("none");
  const [newLinkError, setNewLinkError] = useState<string | null>(null);
  const [savingLink, setSavingLink] = useState(false);
  const [newLinkTags, setNewLinkTags] = useState("");
  const [preview, setPreview] = useState<LinkPreview | null>(null);
  const [previewedUrl, setPreviewedUrl] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [requestMessage, setRequestMessage] = useState<string | null>(null);
  const [pendingRequests, setPendingRequests] = useState<LinkRequest[]>([]);
  const [myRequests, setMyRequests] = useState<LinkRequest[]>([]);
  const [reviewingId, setReviewingId] = useState<number | null>(null);
  const previewRequestRef = useRef(0);

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

  const loadRequests = useCallback(async () => {
    if (!list) {
      setPendingRequests([]);
      setMyRequests([]);
      return;
    }

    if (getToken()) {
      try {
        const mine = await api.get<LinkRequest[]>(
          `/link-requests/mine?list_id=${list.id}`
        );
        setMyRequests(mine);
      } catch {
        setMyRequests([]);
      }
    } else {
      setMyRequests([]);
    }

    const canReview =
      currentUser?.role === "admin" || currentUser?.id === list.user_id;

    if (canReview) {
      try {
        const pending = await api.get<LinkRequest[]>(
          `/link-requests?list_id=${list.id}`
        );
        setPendingRequests(pending);
      } catch {
        setPendingRequests([]);
      }
    } else {
      setPendingRequests([]);
    }
  }, [list, currentUser]);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

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

  async function handleChangeSensitivity(
    linkId: number,
    sensitivity: Sensitivity
  ) {
    try {
      const updated = await api.patch<LinkType>(`/links/${linkId}`, {
        sensitivity,
      });

      setLinks((prev) =>
        prev.map((l) =>
          l.id === linkId ? { ...l, sensitivity: updated.sensitivity } : l
        )
      );
    } catch (err) {
      setVoteMessage(
        err instanceof ApiRequestError
          ? err.message
          : "No se pudo cambiar el tipo de contenido."
      );
    }
  }

  function resetNewLinkForm() {
    setNewLinkTitle("");
    setNewLinkUrl("");
    setNewLinkDescription("");
    setNewLinkTags("");
    setNewLinkSensitivity("none");
    setNewLinkError(null);
    setPreview(null);
    setPreviewedUrl(null);
    setPreviewError(null);
    setRequestMessage(null);
    setShowNewLinkForm(false);
    previewRequestRef.current += 1;
  }

  async function fetchPreview(fill = true): Promise<LinkPreview | null> {
    if (!list) return null;

    const url = newLinkUrl.trim();

    if (!/^https?:\/\//i.test(url)) return null;

    const requestId = previewRequestRef.current + 1;
    previewRequestRef.current = requestId;

    setPreviewLoading(true);
    setPreviewError(null);
    setRequestMessage(null);

    try {
      const data = await api.post<LinkPreview>("/links/preview", {
        url,
        list_id: list.id,
      });

      if (requestId !== previewRequestRef.current) {
        return null;
      }

      setPreview(data);
      setPreviewedUrl(url);

      if (fill) {
        if (data.title && !newLinkTitle.trim()) {
          setNewLinkTitle(data.title);
        }

        if (data.description && !newLinkDescription.trim()) {
          setNewLinkDescription(data.description);
        }

        if (data.tags.length > 0 && !newLinkTags.trim()) {
          setNewLinkTags(data.tags.join(" "));
        }
      }

      return data;
    } catch (err) {
      if (requestId !== previewRequestRef.current) {
        return null;
      }

      setPreview(null);
      setPreviewedUrl(null);
      setPreviewError(
        err instanceof ApiRequestError
          ? err.message
          : "No se pudo leer la página."
      );
      return null;
    } finally {
      if (requestId === previewRequestRef.current) {
        setPreviewLoading(false);
      }
    }
  }

  function parseTagInput(): string[] {
    return newLinkTags
      .split(/\s+/)
      .map((tag) => tag.trim())
      .filter(Boolean);
  }

  async function handleRequestApproval() {
    if (!list) return;

    setSavingLink(true);
    setNewLinkError(null);

    try {
      await api.post<LinkRequest>("/link-requests", {
        list_id: list.id,
        title: newLinkTitle,
        url: newLinkUrl,
        description: newLinkDescription || undefined,
        sensitivity: newLinkSensitivity,
        tags: parseTagInput(),
      });

      resetNewLinkForm();
      setRequestMessage(
        "Solicitud enviada. El propietario de la lista o un admin debe aceptarla."
      );
      await loadRequests();
    } catch (err) {
      setNewLinkError(
        err instanceof ApiRequestError
          ? err.message
          : "No se pudo enviar la solicitud."
      );
    } finally {
      setSavingLink(false);
    }
  }

  async function handleReview(
    requestId: number,
    action: "approve" | "reject"
  ) {
    setReviewingId(requestId);
    setRequestMessage(null);

    try {
      await api.patch<LinkRequest>(`/link-requests/${requestId}`, {
        action,
      });
      await loadData();
      await loadRequests();
    } catch (err) {
      setRequestMessage(
        err instanceof ApiRequestError
          ? err.message
          : "No se pudo revisar la solicitud."
      );
    } finally {
      setReviewingId(null);
    }
  }

  async function handleCreateLink(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setNewLinkError(null);

    if (!list) return;

    if (preview?.belongs === false && !canApprove) {
      await handleRequestApproval();
      return;
    }

    let checked = preview;

    if (!checked && !previewError) {
      checked = await fetchPreview(false);
    }

    if (checked?.belongs === false && !canApprove) {
      return;
    }

    setSavingLink(true);

    try {
      const tags = parseTagInput();

      const newLink = await api.post<LinkType>("/links", {
        list_id: list.id,
        title: newLinkTitle,
        url: newLinkUrl,
        description: newLinkDescription || undefined,
        sensitivity: newLinkSensitivity,
        tags,
      });

      const createdTags =
        tags.length > 0
          ? await api
              .get<Tag[]>(`/links/${newLink.id}/tags`)
              .catch(() => [])
          : [];

      setLinks((prev) => [...prev, { ...newLink, tags: createdTags }]);
      resetNewLinkForm();
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

  const canApprove =
    !!currentUser &&
    !!list &&
    (currentUser.role === "admin" || currentUser.id === list.user_id);

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
                      onClick={() => {
                        resetNewLinkForm();
                        setShowNewLinkForm(true);
                      }}
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

                {canApprove && pendingRequests.length > 0 && (
                  <div className="mb-8 rounded-lg border border-amber-200 bg-amber-50 p-5">
                    <h3 className="mb-3 text-sm font-semibold text-amber-900">
                      Solicitudes pendientes
                    </h3>

                    <div className="space-y-3">
                      {pendingRequests.map((req) => (
                        <div
                          key={req.id}
                          className="rounded-lg border border-amber-200 bg-white p-4"
                        >
                          <div className="flex flex-wrap items-baseline gap-x-2">
                            <a
                              href={req.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="font-medium text-blue-700 hover:underline"
                            >
                              {req.title}
                            </a>

                            <span className="text-xs text-gray-500">
                              por{" "}
                              {req.username ?? `usuario #${req.user_id}`}
                            </span>
                          </div>

                          <p className="mt-1 truncate text-xs text-green-700">
                            {req.url}
                          </p>

                          {req.tags.length > 0 && (
                            <p className="mt-1 text-xs text-gray-500">
                              Tags: {req.tags.join(", ")}
                            </p>
                          )}

                          <div className="mt-3 flex gap-2">
                            <button
                              onClick={() => handleReview(req.id, "approve")}
                              disabled={reviewingId === req.id}
                              className="rounded-full bg-green-700 px-3 py-1 text-xs font-medium text-white transition hover:bg-green-600 disabled:opacity-50"
                            >
                              Aceptar
                            </button>

                            <button
                              onClick={() => handleReview(req.id, "reject")}
                              disabled={reviewingId === req.id}
                              className="rounded-full border border-red-300 px-3 py-1 text-xs text-red-700 transition hover:bg-red-50 disabled:opacity-50"
                            >
                              Rechazar
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {myRequests.length > 0 && (
                  <div className="mb-6 rounded-lg bg-gray-50 px-4 py-3 text-xs text-gray-600">
                    <p className="font-medium text-gray-700">
                      Tus solicitudes en esta lista
                    </p>

                    <ul className="mt-1 space-y-1">
                      {myRequests.map((req) => (
                        <li key={req.id}>
                          {req.title}:{" "}
                          {req.status === "pending"
                            ? "pendiente"
                            : req.status === "approved"
                              ? "aceptada"
                              : "rechazada"}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {requestMessage && (
                  <div className="mb-6 rounded-lg bg-gray-50 px-4 py-2 text-sm text-gray-700">
                    {requestMessage}
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
                      onChange={(e) => {
                        const value = e.target.value;

                        setNewLinkUrl(value);
                        setPreviewError(null);

                        if (
                          previewedUrl &&
                          value.trim() !== previewedUrl
                        ) {
                          if (preview) {
                            if (
                              newLinkTitle === (preview.title ?? "")
                            ) {
                              setNewLinkTitle("");
                            }

                            if (
                              newLinkDescription ===
                              (preview.description ?? "")
                            ) {
                              setNewLinkDescription("");
                            }

                            if (
                              newLinkTags ===
                              preview.tags.join(" ")
                            ) {
                              setNewLinkTags("");
                            }
                          }

                          setPreview(null);
                          setPreviewedUrl(null);
                        }
                      }}
                      onBlur={() => {
                        void fetchPreview();
                      }}
                      placeholder="https://..."
                      required
                      className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm outline-none focus:border-gray-500"
                    />

                    {previewLoading && (
                      <p className="text-xs text-gray-500">
                        Leyendo la página...
                      </p>
                    )}

                    {previewError && (
                      <p className="rounded-lg bg-amber-50 px-4 py-2 text-xs text-amber-800">
                        {previewError} Puedes rellenar los datos a mano y
                        guardar.
                      </p>
                    )}

                    {preview && (
                      <p
                        className={`rounded-lg px-4 py-2 text-xs ${
                          preview.belongs
                            ? "bg-green-50 text-green-800"
                            : "bg-amber-50 text-amber-800"
                        }`}
                      >
                        {preview.reason}
                        {!preview.belongs && canApprove
                          ? " Puedes guardarlo igualmente como propietario o admin."
                          : ""}
                        {!preview.belongs && !canApprove
                          ? " Puedes cancelar o pedir aprobación al propietario de la lista o a un admin."
                          : ""}
                      </p>
                    )}

                    <textarea
                      value={newLinkDescription}
                      onChange={(e) => setNewLinkDescription(e.target.value)}
                      placeholder="Descripción (opcional)"
                      rows={2}
                      className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm outline-none focus:border-gray-500"
                    />

                    <input
                      value={newLinkTags}
                      onChange={(e) => setNewLinkTags(e.target.value)}
                      placeholder="Tags separados por espacio"
                      className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm outline-none focus:border-gray-500"
                    />

                    <select
                      value={newLinkSensitivity}
                      onChange={(e) =>
                        setNewLinkSensitivity(e.target.value as Sensitivity)
                      }
                      className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm outline-none focus:border-gray-500"
                    >
                      {SENSITIVITY_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>

                    {newLinkError && (
                      <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
                        {newLinkError}
                      </p>
                    )}

                    <div className="flex gap-3">
                      {preview?.belongs === false && !canApprove ? (
                        <button
                          type="submit"
                          disabled={savingLink}
                          className="rounded-full bg-amber-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-amber-600 disabled:opacity-50"
                        >
                          {savingLink
                            ? "Enviando..."
                            : "Pedir aprobación"}
                        </button>
                      ) : (
                        <button
                          type="submit"
                          disabled={savingLink}
                          className="rounded-full bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-700 disabled:opacity-50"
                        >
                          {savingLink ? "Guardando..." : "Guardar enlace"}
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={resetNewLinkForm}
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
                              onClick={(e) =>
                                confirmSensitiveOpen(link.sensitivity, e)
                              }
                              className="text-lg font-medium text-blue-700 hover:underline"
                            >
                              {link.title}
                            </a>

                            <SensitivityBadge
                              sensitivity={link.sensitivity}
                            />

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

                          <div className="mt-2">
                            <AiBadge
                                linkId={link.id}
                                score={link.ai_score}
                                checkedAt={link.ai_checked_at}
                                canCheck={!!currentUser}
                                onResult={(updated) =>
                                    setLinks((prev) =>
                                        prev.map((l) =>
                                            l.id === updated.id
                                                ? {
                                                  ...l,
                                                  ai_score: updated.ai_score,
                                                  ai_checked_at: updated.ai_checked_at,
                                                }
                                                : l
                                        )
                                    )
                                }
                            />
                          </div>

                          {link.description && (
                            <p className="mt-2 text-sm text-gray-600">
                              {link.description}
                            </p>
                          )}

                          {(currentUser?.role === "admin" ||
                            currentUser?.role === "moderator") && (
                            <select
                              value={link.sensitivity ?? "none"}
                              onChange={(e) =>
                                handleChangeSensitivity(
                                  link.id,
                                  e.target.value as Sensitivity
                                )
                              }
                              aria-label="Tipo de contenido"
                              className="mt-3 rounded-full border border-gray-300 px-3 py-1 text-xs text-gray-700 outline-none focus:border-gray-500"
                            >
                              {SENSITIVITY_OPTIONS.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                  {opt.label}
                                </option>
                              ))}
                            </select>
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
