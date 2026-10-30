"use client";

import { useState } from "react";
import { api } from "@/app/lib/api";
import { Link as LinkType } from "@/app/lib/types";

type Props = {
    linkId: number;
    score: number | null;
    checkedAt: string | null;
    canCheck: boolean;
    onResult: (link: LinkType) => void;
};

const BASE =
    "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium";

export default function AiBadge({
                                    linkId,
                                    score,
                                    checkedAt,
                                    canCheck,
                                    onResult,
                                }: Props) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleCheck() {
        setLoading(true);
        setError(null);

        try {
            const updated = await api.post<LinkType>(`/links/${linkId}/ai-check`);
            onResult(updated);
        } catch (err) {
            setError(err instanceof Error ? err.message : "No se pudo analizar");
        } finally {
            setLoading(false);
        }
    }

    if (checkedAt && score !== null) {
        const color =
            score < 30
                ? "bg-green-100 text-green-800"
                : score < 60
                    ? "bg-yellow-100 text-yellow-800"
                    : "bg-red-100 text-red-800";

        return (
            <span
                className={`${BASE} ${color}`}
                title="Estimación automática; no es una certificación"
            >
        Contenido IA: ~{score}% (estimación)
      </span>
        );
    }

    if (checkedAt) {
        return (
            <span className={`${BASE} bg-gray-100 text-gray-600`}>
        Texto insuficiente para analizar
      </span>
        );
    }

    if (!canCheck) {
        return null;
    }

    return (
        <div className="flex items-center gap-2">
            <button
                type="button"
                onClick={handleCheck}
                disabled={loading}
                className={`${BASE} border border-gray-300 text-gray-700 hover:bg-gray-100 disabled:opacity-50`}
            >
                {loading ? "Analizando..." : "Analizar contenido IA"}
            </button>
            {error && <span className="text-xs text-red-600">{error}</span>}
        </div>
    );
}