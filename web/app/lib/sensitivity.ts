import type { Sensitivity } from "@/app/lib/types";

export const SENSITIVITY_OPTIONS: { value: Sensitivity; label: string }[] = [
  { value: "none", label: "Sin contenido sensible" },
  { value: "adult", label: "Contenido +18" },
  { value: "violence", label: "Contenido violento" },
];

const WARNINGS: Record<Exclude<Sensitivity, "none">, string> = {
  adult:
    "Este enlace puede contener contenido para mayores de 18 años.\n\n¿Quieres continuar?",
  violence:
    "Este enlace puede contener contenido violento o perturbador.\n\n¿Quieres continuar?",
};

/**
  si el enlace es sensible pide confirmacion y cancela la navegacion si el usuario dice que no.
 */
export function confirmSensitiveOpen(
  sensitivity: Sensitivity | undefined,
  event: React.MouseEvent<HTMLAnchorElement>
): void {
  if (!sensitivity || sensitivity === "none") return;

  if (!window.confirm(WARNINGS[sensitivity])) {
    event.preventDefault();
  }
}