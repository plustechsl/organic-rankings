"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import Navbar from "@/app/components/Navbar";
import Logo from "@/app/components/Logo";

const PRESET_AMOUNTS = [3, 5, 10, 25];

const DONATE_URL = process.env.NEXT_PUBLIC_DONATE_URL ?? "";

export default function DonatePage() {
  const [amount, setAmount] = useState(5);
  const [customAmount, setCustomAmount] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleDonate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!DONATE_URL) {
      setError("El pago de donaciones todavía no está configurado.");
      return;
    }

    const value = customAmount ? Number(customAmount) : amount;

    if (!value || value <= 0) {
      setError("Introduce un importe válido.");
      return;
    }

    const target = DONATE_URL.includes("{amount}")
      ? DONATE_URL.replace("{amount}", String(value))
      : DONATE_URL;

    window.location.href = target;
  }

  return (
    <main className="min-h-screen bg-white text-gray-900">
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-8 px-6 py-5">
          <Link
            href="/"
            className="flex flex-shrink-0 items-center gap-2 text-xl font-semibold tracking-tight"
          >
            <Logo className="h-6 w-6" />
            Organic Rankings
          </Link>

          <Navbar />
        </div>
      </header>

      <section className="mx-auto max-w-xl px-6 py-12">
        <h1 className="mb-3 text-3xl font-semibold tracking-tight">
          Donar a Organic Rankings
        </h1>

        <p className="mb-8 text-gray-500">
          Organic Rankings no lleva publicidad ni vende posiciones. Si te resulta
          útil, puedes apoyar el proyecto con una donación. El pago se completa
          en una plataforma externa segura.
        </p>

        <form onSubmit={handleDonate} className="space-y-6">
          <div>
            <p className="mb-2 text-sm text-gray-600">Elige un importe</p>

            <div className="flex flex-wrap gap-3">
              {PRESET_AMOUNTS.map((value) => {
                const selected = !customAmount && amount === value;

                return (
                  <button
                    key={value}
                    type="button"
                    onClick={() => {
                      setAmount(value);
                      setCustomAmount("");
                    }}
                    className={`rounded-full border px-5 py-2 text-sm font-medium transition ${
                      selected
                        ? "border-gray-900 bg-gray-900 text-white"
                        : "border-gray-300 text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    {value} €
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label
              htmlFor="custom-amount"
              className="mb-1 block text-sm text-gray-600"
            >
              Otro importe (€)
            </label>
            <input
              id="custom-amount"
              type="number"
              min={1}
              step={1}
              value={customAmount}
              onChange={(e) => setCustomAmount(e.target.value)}
              placeholder="Ej: 15"
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 outline-none focus:border-gray-500"
            />
          </div>

          {error && (
            <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          <button
            type="submit"
            className="w-full rounded-full bg-gray-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-gray-700"
          >
            Donar
          </button>

          <p className="text-center text-xs text-gray-400">
            Serás redirigido a la plataforma de pago para completar la donación.
          </p>
        </form>
      </section>
    </main>
  );
}
