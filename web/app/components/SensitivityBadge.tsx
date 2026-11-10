"use client";

import { useLang } from "@/app/lib/lang";
import type { Sensitivity } from "@/app/lib/types";

const CLASSES: Record<Exclude<Sensitivity, "none">, string> = {
  adult: "bg-red-100 text-red-700",
  violence: "bg-orange-100 text-orange-700",
};

export default function SensitivityBadge({
  sensitivity,
}: {
  sensitivity: Sensitivity | undefined;
}) {
  const { t } = useLang();

  if (!sensitivity || sensitivity === "none") return null;

  const badgeText =
    sensitivity === "adult" ? "+18" : t.sensitivity.badgeViolence;

  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${CLASSES[sensitivity]}`}
      title={t.sensitivity.badgeTitle}
    >
      {badgeText}
    </span>
  );
}
