"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/app/components/Navbar";
import { api, getToken, ApiRequestError } from "@/app/lib/api";
import { AdminInvitation } from "@/app/lib/types";

type CurrentUser = {
  id: number;
  username: string;
  email: string;
  role: string;
};

type InvitationFilter = "pending" | "all";

function statusLabel(status: string): string {
  if (status === "approved") {
    return "Aprobada";
  }
  if (status === "rejected") {
    return "Rechazada";
  }
  return "Pendiente";
}

function statusBadgeClass(status: string): string {
  if (status === "approved") {
    return "rounded-full bg-green-50 px-2.5 py-1 text-xs text-green-700";
  }
  if (status === "rejected") {
    return "rounded-full bg-red-50 px-2.5 py-1 text-xs text-red-700";
  }
  return "rounded-full bg-yellow-50 px-2.5 py-1 text-xs text-yellow-700";
}

export default function AdminPage() {
  const router = useRouter();

  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [filter, setFilter] = useState<InvitationFilter>("pending");
  const [invitations, setInvitations] = useState<AdminInvitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actingId, setActingId] = useState<number | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
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
        setError("No se pudo cargar tu cuenta.");
        setLoading(false);
      }
    }

    load();
  }, [router]);

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
          setError("No se pudieron cargar las invitaciones.");
        }
      } finally {
        setLoading(false);
      }
    }

    loadInvitations();
  }, [allowed, filter]);

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
        setError("No se pudo procesar la invitación.");
      }
    } finally {
      setActingId(null);
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
        <h1 className="mb-2 text-2xl font-semibold">Administración</h1>
        <p className="mb-8 text-sm text-gray-500">
          Valida las invitaciones para conceder los puntos al usuario que invitó.
        </p>

        {allowed === null && (
          <p className="text-sm text-gray-500">Cargando...</p>
        )}

        {allowed === false && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            No tienes permisos de administrador.
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
                Pendientes
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
                Todas
              </button>
            </div>

            {error && (
              <p className="mb-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
                {error}
              </p>
            )}

            {loading && <p className="text-sm text-gray-500">Cargando...</p>}

            {!loading && invitations.length === 0 && (
              <p className="text-sm text-gray-500">
                No hay invitaciones {filter === "pending" ? "pendientes" : ""}.
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
                        <span className="font-medium">
                          {invitation.inviter_username ??
                            `Usuario #${invitation.inviter_id}`}
                        </span>{" "}
                        invitó a{" "}
                        <span className="font-medium">
                          {invitation.invited_username ??
                            `Usuario #${invitation.invited_user_id}`}
                        </span>
                      </p>
                      <p className="text-xs text-gray-400">
                        {new Date(invitation.created_at).toLocaleDateString(
                          "es-ES"
                        )}{" "}
                        · {invitation.points} puntos
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
                            Aprobar
                          </button>

                          <button
                            type="button"
                            disabled={actingId === invitation.id}
                            onClick={() => handleReview(invitation.id, "reject")}
                            className="rounded-full border border-gray-300 px-4 py-1.5 text-sm text-gray-700 transition hover:bg-gray-50 disabled:opacity-50"
                          >
                            Rechazar
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </section>
    </main>
  );
}
