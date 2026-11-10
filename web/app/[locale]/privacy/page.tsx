import Link from "next/link";
import Navbar from "@/app/components/Navbar";
import Logo from "@/app/components/Logo";

export const metadata = {
  title: "Política de privacidad | Organic Rankings",
  description: "Política de privacidad de Organic Rankings",
};

export default function PrivacyPage() {
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

      <section className="mx-auto max-w-3xl px-6 py-12">
        <h1 className="mb-2 text-3xl font-semibold tracking-tight">
          Política de privacidad
        </h1>

        <p className="mb-10 text-sm text-gray-500">
          Última actualización: 09/10/2026
        </p>

        <article className="space-y-8 text-gray-700">
          <div>
            <h2 className="mb-2 text-lg font-semibold text-gray-900">
              1. Responsable
            </h2>
            <p>
              Organic Rankings es una plataforma comunitaria para crear, votar y
              descubrir listas temáticas de recursos web.
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold text-gray-900">
              2. Datos que recopilamos
            </h2>
            <ul className="list-disc space-y-1 pl-6">
              <li>
                <strong>Datos de registro:</strong> nombre de usuario, email y
                contraseña cifrada.
              </li>
              <li>
                <strong>Contenido de usuario:</strong> listas, enlaces, votos,
                especialidades y reputación.
              </li>
              <li>
                <strong>Datos técnicos mínimos:</strong> los necesarios para
                mantener la sesión y prevenir abusos.
              </li>
            </ul>
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold text-gray-900">
              3. Finalidad del tratamiento
            </h2>
            <ul className="list-disc space-y-1 pl-6">
              <li>Gestionar tu cuenta y tu sesión.</li>
              <li>Permitir crear, votar y visualizar listas y enlaces.</li>
              <li>Gestionar especialidades y reputación.</li>
              <li>Prevenir abusos, spam y votaciones fraudulentas.</li>
              <li>Ofrecer el buscador interno de la plataforma.</li>
            </ul>
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold text-gray-900">
              4. Almacenamiento y seguridad
            </h2>
            <p>
              Los datos se almacenan en PostgreSQL. Las contraseñas se guardan
              siempre cifradas. El contenido público se indexa en la propia base
              de datos para que el buscador interno funcione.
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold text-gray-900">
              5. Sesión y cookies
            </h2>
            <p>
              Usamos el almacenamiento local del navegador (localStorage) para
              guardar el token que mantiene tu sesión iniciada. No usamos cookies
              de seguimiento, publicidad ni analítica de terceros.
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold text-gray-900">
              6. Enlaces a terceros
            </h2>
            <p>
              La página de <Link href="/donate">Donaciones</Link> redirige a una
              pasarela de pago externa; al usarla, quedas sujeto a su propia
              política de privacidad. Los enlaces de las listas apuntan a sitios
              externos, de cuyo contenido no somos responsables.
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold text-gray-900">
              7. Compartición de datos
            </h2>
            <p>
              No vendemos ni compartimos tus datos personales. Únicamente se
              muestra la información necesaria para el funcionamiento
              comunitario de la plataforma.
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold text-gray-900">
              8. Tus derechos
            </h2>
            <p>
              Puedes solicitar el acceso, la rectificación o la eliminación de
              tus datos escribiendo al responsable de la plataforma.
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold text-gray-900">
              9. Cambios en esta política
            </h2>
            <p>
              Esta política puede actualizarse. Cualquier cambio se publicará en
              esta misma página junto con su fecha de actualización.
            </p>
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold text-gray-900">
              10. Contacto
            </h2>
            <p>
              Para cualquier duda sobre esta política, utiliza los canales de
              contacto habilitados en la plataforma.
            </p>
          </div>
        </article>
      </section>
    </main>
  );
}
