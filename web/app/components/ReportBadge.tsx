"use client";

import { useState } from "react";
import { api, ApiRequestError } from "@/app/lib/api";
import { useLang } from "@/app/lib/lang";
import { DATE_LOCALES, format } from "@/app/lib/i18n";
import {
    REPORT_REASONS,
    ReportReason,
    ReportResponse,
    VerificationStatus,
} from "@/app/lib/types";

type Props = {
    linkId: number;
    reportCount: number;
    verificationStatus: VerificationStatus | null;
    verifiedAt: string | null;
    verifiedBy: string | null;
    canReport: boolean;
    onResult: (result: ReportResponse) => void;
};

const BASE =
    "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium";

export default function ReportBadge({
                                        linkId,
                                        reportCount,
                                        verificationStatus,
                                        verifiedAt,
                                        verifiedBy,
                                        canReport,
                                        onResult,
                                    }: Props) {
    const { t, locale } = useLang();

    const [open, setOpen] = useState(false);
    const [reason, setReason] = useState<ReportReason>("fuente_dudosa");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [done, setDone] = useState(false);

    async function handleSubmit() {
        setLoading(true);
        setError(null);

        try {
            const result = await api.post<ReportResponse>(
                `/links/${linkId}/report`,
                { reason }
            );
            onResult(result);
            setDone(true);
            setOpen(false);
        } catch (err) {
            setError(
                err instanceof ApiRequestError ? err.message : t.report.error
            );
        } finally {
            setLoading(false);
        }
    }

    const countText =
        reportCount === 1
            ? t.report.countOne
            : format(t.report.countMany, { count: reportCount });

    return (
        <div className="flex flex-wrap items-center gap-2">
            {reportCount > 0 && (
                <span
                    className={`${BASE} bg-gray-100 text-gray-600`}
                    title={t.report.adminIntro}
                >
                    {countText}
                </span>
            )}

            {verificationStatus && (
                <span
                    className={`${BASE} ${
                        verificationStatus === "fiable"
                            ? "bg-green-100 text-green-800"
                            : "bg-amber-100 text-amber-800"
                    }`}
                >
                    {format(t.report.reviewed, {
                        verdict: t.report[verificationStatus],
                    })}
                    {verifiedBy ? ` · ${format(t.report.by, { user: verifiedBy })}` : ""}
                    {verifiedAt
                        ? ` · ${new Date(verifiedAt).toLocaleDateString(
                              DATE_LOCALES[locale]
                          )}`
                        : ""}
                </span>
            )}

            {canReport && !open && (
                <button
                    type="button"
                    onClick={() => {
                        setError(null);
                        setOpen(true);
                    }}
                    className={`${BASE} border border-gray-300 text-gray-600 hover:bg-gray-50`}
                >
                    {done ? t.report.done : t.report.button}
                </button>
            )}

            {canReport && open && (
                <div className="flex flex-wrap items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2">
                    <label className="text-xs text-gray-600" htmlFor={`report-reason-${linkId}`}>
                        {t.report.reasonLabel}
                    </label>

                    <select
                        id={`report-reason-${linkId}`}
                        value={reason}
                        onChange={(event) =>
                            setReason(event.target.value as ReportReason)
                        }
                        className="rounded-full border border-gray-300 bg-white px-2 py-1 text-xs outline-none focus:border-gray-500"
                    >
                        {REPORT_REASONS.map((value) => (
                            <option key={value} value={value}>
                                {t.report.reasons[value]}
                            </option>
                        ))}
                    </select>

                    <button
                        type="button"
                        onClick={handleSubmit}
                        disabled={loading}
                        className="rounded-full bg-gray-900 px-3 py-1 text-xs font-medium text-white transition hover:bg-gray-700 disabled:opacity-50"
                    >
                        {loading ? t.common.saving : t.report.send}
                    </button>

                    <button
                        type="button"
                        onClick={() => {
                            setOpen(false);
                            setError(null);
                        }}
                        className="rounded-full border border-gray-300 px-3 py-1 text-xs text-gray-700 transition hover:bg-white"
                    >
                        {t.report.cancel}
                    </button>

                    {error && <span className="text-xs text-red-600">{error}</span>}
                </div>
            )}
        </div>
    );
}
