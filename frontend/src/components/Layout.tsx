import { NavLink, Outlet } from "react-router-dom";

import { ThemeToggle } from "./ThemeToggle";

const LINKS = [
  { to: "/", label: "Mapa", end: true },
  { to: "/resultados", label: "Resultados", end: false },
  { to: "/secoes", label: "Seções e boletins", end: false },
  { to: "/analises", label: "Análises", end: false },
  { to: "/dados-abertos", label: "Dados abertos", end: false },
];

export function Layout() {
  return (
    <>
      <a className="skip-link" href="#conteudo">
        Pular para o conteúdo
      </a>
      <header className="topbar">
        <div className="topbar__inner">
          <NavLink to="/" className="brand" aria-label="Eleições 2026, mapa dos resultados">
            <span className="brand__mark" aria-hidden="true">
              ✓
            </span>
            <span>
              Eleições 2026 <small>dados públicos do TSE</small>
            </span>
          </NavLink>
          <nav aria-label="Principal">
            <ul className="nav">
              {LINKS.map((link) => (
                <li key={link.to}>
                  <NavLink to={link.to} end={link.end} className="nav__link">
                    {link.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
          <ThemeToggle />
        </div>
      </header>
      <main id="conteudo" className="page">
        <Outlet />
      </main>
      <footer className="footer">
        Fonte: Tribunal Superior Eleitoral: portal de resultados e Portal de Dados Abertos. Os boletins são
        lidos do arquivo oficial assinado de cada urna.
      </footer>
    </>
  );
}
