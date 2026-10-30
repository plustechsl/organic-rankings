import type { Sensitivity } from "@/app/lib/types";

const BADGES: Record<Exclude<Sensitivity, "none">, { text: string; cls: string }> = {
  adult: { text: "+18", cls: "bg-red-100 text-red-700" },
  violence: { text: "Violencia", cls: "bg-orange-100 text-orange-700" },
};

export default function SensitivityBadge({
  sensitivity,
}: {
  sensitivity: Sensitivity | undefined;
}) {
  if (!sensitivity || sensitivity === "none") return null;

  const badge = BADGES[sensitivity];

  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${badge.cls}`}
      title="Contenido sensible"
    >
      {badge.text}
    </span>
  );
}