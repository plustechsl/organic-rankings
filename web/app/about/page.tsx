import Link from "next/link";
import Navbar from "@/app/components/Navbar";
import Logo from "@/app/components/Logo";

const principles = [
  {
    title: "Rankings hechos por humanos",
    text: "Ninguna posición la decide un bot ni una fórmula oculta.",
  },
  {
    title: "Nada se compra",
    text: "No se vende visibilidad: ningún resultado sube por pagar.",
  },
  {
    title: "El SEO no cuenta",
    text: "Un recurso sube si ayuda a las personas, no si está optimizado para buscadores.",
  },
  {
    title: "Vota con criterio",
    text: "Vota lo que te haya servido de verdad, no por amistad ni por interés.",
  },
  {
    title: "Una persona, un voto",
    text: "Nada de cuentas múltiples, bots ni votos organizados.",
  },
  {
    title: "La experiencia pesa, con honestidad",
    text: "Los especialistas valen más en su campo (x3). Declara solo las especialidades que de verdad tienes.",
  },
  {
    title: "Aporta enlaces útiles",
    text: "Descripciones fieles, sin spam ni autopromoción disfrazada.",
  },
  {
    title: "Transparencia",
    text: "Las reglas son públicas y el proyecto es de código abierto. Las listas iniciales se generan automáticamente con cero puntos: la clasificación la ponen las personas.",
  },
];

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-white text-gray-900">
      <header className="border-b border-gray-200">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-5">
          <Link
            href="/"
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
          Sobre el proyecto
        </h1>

        <p className="mb-12 text-lg leading-8 text-gray-600">
          Organic Rankings es una plataforma abierta de listas de recursos web
          ordenadas por personas. Cualquiera puede crear listas, añadir enlaces
          y votarlos, y la puntuación de cada recurso la decide la comunidad:
          no un algoritmo opaco, ni técnicas de SEO, ni quien más paga.
        </p>

        <h2 className="mb-6 text-xl font-semibold">Nuestros principios</h2>

        <ol className="space-y-5">
          {principles.map((principle, index) => (
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
