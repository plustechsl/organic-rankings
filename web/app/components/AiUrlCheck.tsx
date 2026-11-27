"use client";

import { useState } from "react";
import { api, ApiRequestError } from "@/app/lib/api";
import { useLang } from "@/app/lib/lang";
import { format } from "@/app/lib/i18n";
import { AiUrlCheckResult } from "@/app/lib/types";

type CheckState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "done"; result: AiUrlCheckResult };

export function normalizeUrl(raw: string): string | null {
  const value = raw.trim();

  if (!value || /\s/.test(value)) {
    return null;
  }

  const withScheme = /^https?:\/\//i.test(value) ? value : `https://${value}`;

  try {
    const url = new URL(withScheme);

    if (!url.hostname.includes(".")) {
      return null;
    }

    return url.toString();
  } catch {
    return null;
  }
}

export function useAiUrlCheck() {
  const { t } = useLang();
  const [state, setState] = useState<CheckState>({ status: "idle" });

  async function run(raw: string) {
    if (!raw.trim()) {
      setState({ status: "error", message: t.aiUrl.emptyUrl });
      return;
    }

    const url = normalizeUrl(raw);

    if (!url) {
      setState({ status: "error", message: t.aiUrl.invalidUrl });
      return;
    }

    setState({ status: "loading" });

    try {
      const result = await api.post<AiUrlCheckResult>("/links/ai-check-url", {
        url,
      });
      setState({ status: "done", result });
    } catch (err) {
      const message =
        err instanceof ApiRequestError && err.status === 429
          ? t.aiUrl.tooMany
          : err instanceof Error
            ? err.message
            : t.aiUrl.error;

      setState({ status: "error", message });
    }
  }

  function reset() {
    setState({ status: "idle" });
  }

  return { state, run, reset };
}

type ButtonProps = {
  loading: boolean;
  onClick: () => void;
};

export function AiUrlButton({ loading, onClick }: ButtonProps) {
  const { t } = useLang();

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={loading}
      aria-label={t.aiUrl.buttonAria}
      className="ml-2 shrink-0 rounded-full border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:border-gray-400 hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-900 disabled:cursor-wait disabled:opacity-60 sm:px-5 sm:py-2.5"
    >
      {loading ? t.aiUrl.analyzing : t.aiUrl.button}
    </button>
  );
}

function scoreColors(score: number) {
  if (score < 30) {
    return { bar: "bg-green-600", text: "text-green-800" };
  }

  if (score < 60) {
    return { bar: "bg-yellow-500", text: "text-yellow-800" };
  }

  return { bar: "bg-red-600", text: "text-red-800" };
}

type PanelProps = {
  state: CheckState;
  onClose: () => void;
};

export function AiUrlResultPanel({ state, onClose }: PanelProps) {
  const { t } = useLang();

  if (state.status === "idle" || state.status === "loading") {
    return null;
  }

  if (state.status === "error") {
    return (
      <div
        role="alert"
        className="flex items-start justify-between gap-4 rounded-lg border border-red-200 bg-red-50 p-4 text-left text-sm text-red-700"
      >
        <span>{state.message}</span>
        <button
          type="button"
          onClick={onClose}
          className="shrink-0 text-red-700 underline hover:text-red-900"
        >
          {t.aiUrl.close}
        </button>
      </div>
    );
  }

  const { result } = state;
  const signalLabels = t.aiUrl.signals as Record<string, string>;

  const header = (
    <div className="flex items-start justify-between gap-4">
      <div className="min-w-0">
        <p className="text-sm font-medium text-gray-900">{t.aiUrl.title}</p>
        <p className="mt-1 truncate text-xs text-gray-500" title={result.url}>
          {result.url}
        </p>
      </div>
      <button
        type="button"
        onClick={onClose}
        className="shrink-0 text-xs text-gray-500 underline hover:text-gray-900"
      >
        {t.aiUrl.close}
      </button>
    </div>
  );

  if (!result.enough_text || result.score === null) {
    return (
      <div
        role="status"
        className="rounded-2xl border border-gray-200 bg-white p-5 text-left"
      >
        {header}
        <p className="mt-4 text-sm text-gray-700">
          {format(t.aiUrl.insufficient, {
            words: result.words,
            min: result.min_words,
          })}
        </p>
      </div>
    );
  }

  const colors = scoreColors(result.score);
  const verdict =
    result.score < 30
      ? t.aiUrl.labelLow
      : result.score < 60
        ? t.aiUrl.labelMixed
        : t.aiUrl.labelHigh;

  const signals = Object.entries(result.signals).filter(
    (entry): entry is [string, number] => entry[1] !== null
  );

  return (
    <div
      role="status"
      className="rounded-2xl border border-gray-200 bg-white p-5 text-left"
    >
      {header}

      <div className="mt-4 flex items-baseline gap-3">
        <span className={`text-4xl font-semibold tabular-nums ${colors.text}`}>
          {result.score}%
        </span>
        <span className="text-sm text-gray-700">{verdict}</span>
      </div>

      <div
        className="mt-3 h-2 w-full overflow-hidden rounded-full bg-gray-100"
        role="meter"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={result.score}
        aria-label={t.aiUrl.title}
      >
        <div
          className={`h-full rounded-full ${colors.bar}`}
          style={{ width: `${result.score}%` }}
        />
      </div>

      <p className="mt-3 text-xs text-gray-500">
        {format(t.aiUrl.words, { words: result.words })}
        <br />
        {format(t.aiUrl.confidence, {
          confidence: Math.round((result.confidence ?? 0) * 100),
        })}
      </p>

      {signals.length > 0 && (
        <div className="mt-5">
          <p className="mb-2 text-xs font-medium text-gray-700">
            {t.aiUrl.signalsTitle}
          </p>
          <ul className="space-y-2">
            {signals.map(([key, value]) => (
              <li key={key} className="flex items-center gap-3 text-xs">
                <span className="w-48 shrink-0 text-gray-600">
                  {signalLabels[key] ?? key}
                </span>
                <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-gray-100">
                  <span
                    className="block h-full rounded-full bg-gray-500"
                    style={{ width: `${Math.round(value * 100)}%` }}
                  />
                </span>
                <span className="w-9 shrink-0 text-right tabular-nums text-gray-500">
                  {Math.round(value * 100)}%
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="mt-5 text-xs text-gray-400">{t.aiUrl.disclaimer}</p>
    </div>
  );
}