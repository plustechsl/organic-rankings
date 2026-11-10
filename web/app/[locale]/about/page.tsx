import Link from "next/link";
import Navbar from "@/app/components/Navbar";
import Logo from "@/app/components/Logo";
import { getDictionary } from "@/app/lib/dictionaries";
import { isLocale, localePath } from "@/app/lib/i18n";

type PageParams = { params: Promise<{ locale: string }> };

export default async function AboutPage({ params }: PageParams) {
  const { locale } = await params;

  if (!isLocale(locale)) {
    return null;
  }

  const t = getDictionary(locale);

  return (
    <main className="min-h-screen bg-white text-gray-900">
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-5">
          <Link
            href={localePath(locale, "/")}
            className="flex items-center gap-2 text-xl font-semibold tracking-tight"
          >
            <Logo className="h-6 w-6" />
            Organic Rankings
          </Link>

          <Navbar />
        </div>
      </header>

      <section className="mx-auto max-w-3xl px-6 py-12">
        <h1 className="mb-4 text-3xl font-semibold tracking-tight">
          {t.about.title}
        </h1>

        <p className="mb-12 text-lg leading-8 text-gray-600">
          {t.about.intro}
        </p>

        <h2 className="mb-6 text-xl font-semibold">{t.about.principlesTitle}</h2>

        <ol className="space-y-5">
          {t.about.principles.map((principle, index) => (
            <li key={principle.title} className="flex gap-4">
              <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gray-900 text-sm font-medium text-white">
                {index + 1}
              </span>

              <div>
                <h3 className="font-medium">{principle.title}</h3>
                <p className="text-sm leading-6 text-gray-600">
                  {principle.text}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
