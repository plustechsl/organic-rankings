"use client";

import { useEffect, useState } from "react";
import { Ad, pickAd } from "@/app/lib/ads";

type Props = {
  themeSlug?: string | null;
};

export default function AdSlot({ themeSlug }: Props) {
  const [ad, setAd] = useState<Ad | null>(null);

  useEffect(() => {
    setAd(pickAd(themeSlug ?? undefined));
  }, [themeSlug]);

  return (
    <div className="w-full rounded-lg border border-gray-300 bg-white p-2 shadow-sm">
      <div className="mb-1 flex items-center justify-between">
        <p className="text-[10px] uppercase tracking-[0.2em] text-gray-400">
          Publicidad
        </p>
        <span className="text-[10px] text-gray-400">Ad</span>
      </div>
      <div className="flex min-h-[250px] items-center justify-center rounded-md bg-gray-50">
        {ad ? (
          <>
            {ad.iframeSrc ? (
              <iframe
                src={ad.iframeSrc}
                title={ad.alt || ad.title || "Publicidad"}
                className="h-[250px] w-full rounded-md border-0"
                sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
              />
            ) : ad.imageUrl && ad.href ? (
              <a
                href={ad.href}
                target="_blank"
                rel="noopener noreferrer"
                className="block h-[250px] w-full"
              >
                <img
                  src={ad.imageUrl}
                  alt={ad.alt || ad.title || "Publicidad"}
                  className="h-[250px] w-full rounded-md object-cover"
                />
              </a>
            ) : ad.html ? (
              <div
                className="w-full px-2 text-center text-sm text-gray-700"
                dangerouslySetInnerHTML={{ __html: ad.html }}
              />
            ) : (
              <div className="w-full px-2 text-center text-sm text-gray-700">
                {ad.title && <p className="font-medium">{ad.title}</p>}
                {ad.text && <p className="mt-1">{ad.text}</p>}
              </div>
            )}
          </>
        ) : (
          <p className="text-center text-xs text-gray-400">Espacio publicitario</p>
        )}
      </div>
    </div>
  );
}
