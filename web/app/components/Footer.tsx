export default function Footer() {
  return (
    <footer className=\"mt-auto border-t border-gray-100 bg-white\">
      <div className=\"mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-6 text-sm text-gray-500 sm:flex-row\">
        <p>© {new Date().getFullYear()} Organic Rankings</p>
        <div className=\"flex items-center gap-4\">
          <a href=\"/privacy\" className=\"transition hover:text-gray-900\">
            Política de privacidad
          </a>
          <a href=\"/donate\" className=\"transition hover:text-gray-900\">
            Donar
          </a>
        </div>
      </div>
    </footer>
  );
}
