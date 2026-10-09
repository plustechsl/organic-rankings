import Navbar from '@/app/components/Navbar';
import Logo from '@/app/components/Logo';
import Footer from '@/app/components/Footer';

export const metadata = {
  title: 'Política de privacidad | Organic Rankings',
  description: 'Política de privacidad de Organic Rankings',
};

export default function PrivacyPage() {
  return (
    <main className=\"min-h-screen bg-white\">
      <Navbar />
      <section className=\"mx-auto max-w-3xl px-4 py-12\">
        <div className=\"mb-10 text-center\">
          <Logo />
          <p className=\"mt-2 text-sm text-gray-500\">Política de privacidad</p>
        </div>

        <article className=\"prose prose-sm prose-gray max-w-none\">
          <p className=\"text-sm text-gray-500\">Última actualización: 09/10/2026</p>

          <h2>1. Responsable</h2>
          <p>Organic Rankings es una plataforma comunitaria para crear y votar listas temáticas de recursos web.</p>

          <h2>2. Datos que recopilamos</h2>
          <ul>
            <li><strong>Datos de registro:</strong> nombre de usuario, email y contraseña cifrada.</li>
            <li><strong>Contenido de usuario:</strong> listas, enlaces, votos, especialidades y reputación.</li>
            <li><strong>Datos técnicos mínimos:</strong> necesarios para mantener la sesión.</li>
          </ul>

          <h2>3. Finalidad</h2>
          <ul>
            <li>Gestionar tu cuenta.</li>
            <li>Permitir creación, votación y visualización de listas y enlaces.</li>
            <li>Mantener reputación y especialidades.</li>
            <li>Prevenir abusos.</li>
            <li>Ofrecer búsqueda interna mediante indexación pública.</li>
          </ul>

          <h2>4. Almacenamiento y seguridad</h2>
          <p>Los datos se almacenan en PostgreSQL. Las contraseñas siempre se guardan cifradas.</p>
          <p>El contenido público se indexa en OpenSearch para el buscador interno.</p>

          <h2>5. Sesión</h2>
          <p>Usamos localStorage para guardar el token JWT y mantener tu sesión.</p>
          <p>No usamos cookies de seguimiento, publicidad ni analítica de terceros.</p>

          <h2>6. Enlaces a terceros</h2>
          <p>La página de <a href=\"/donate\">Donar</a> redirige a una pasarela externa. Al usarla, quedas sujeto a su política de privacidad.</p>
          <p>Los enlaces de las listas son externos. No nos responsabilizamos de su contenido.</p>

          <h2>7. Compartición</h2>
          <p>No vendemos ni compartimos datos personales. Solo se muestra lo necesario para el funcionamiento comunitario.</p>

          <h2>8. Derechos</h2>
          <p>Puedes solicitar acceso, rectificación o eliminación escribiendo al responsable.</p>

          <h2>9. Cambios</h2>
          <p>Esta política puede actualizarse y se publicará en esta página con su fecha.</p>

          <h2>10. Contacto</h2>
          <p>Para dudas sobre esta política, usa los canales habilitados.</p>
        </article>
      </section>
    </main>
  );
}
