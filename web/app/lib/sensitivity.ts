import type { Sensitivity } from "@/app/lib/types";

export const SENSITIVITY_VALUES: Sensitivity[] = ["none", "adult", "violence"];

/**
  si el enlace es sensible pide confirmacion y cancela la navegacion si el usuario dice que no.
 */
export function confirmSensitiveOpen(
  sensitivity: Sensitivity | undefined,
  event: React.MouseEvent<HTMLAnchorElement>,
  warnAdult: string,
  warnViolence: string
): void {
  if (!sensitivity || sensitivity === "none") return;

  const warning = sensitivity === "adult" ? warnAdult : warnViolence;

  if (!window.confirm(warning)) {
    event.preventDefault();
  }
}
