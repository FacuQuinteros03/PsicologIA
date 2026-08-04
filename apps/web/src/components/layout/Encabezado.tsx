'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import estilos from './Encabezado.module.css';

const ENLACES = [{ href: '/', etiqueta: 'Pacientes' }];

export function Encabezado() {
  const ruta = usePathname();

  return (
    <header className={estilos.barra}>
      <Link href="/" className={estilos.marca}>
        <span className={estilos.logo} aria-hidden="true" />
        PsicoIA
      </Link>

      <nav className={estilos.navegacion} aria-label="Principal">
        {ENLACES.map((enlace) => {
          const activo = enlace.href === '/' ? ruta === '/' : ruta.startsWith(enlace.href);
          return (
            <Link
              key={enlace.href}
              href={enlace.href}
              className={`${estilos.enlace} ${activo ? estilos.activo : ''}`}
              aria-current={activo ? 'page' : undefined}
            >
              {enlace.etiqueta}
            </Link>
          );
        })}
      </nav>

      {/* Placeholder del usuario. Cuando entre el login, sale de la sesión. */}
      <div className={estilos.usuario} title="Sin autenticación todavía">
        <span className={estilos.avatar} aria-hidden="true">
          LD
        </span>
        <span className={estilos.nombreUsuario}>Lic. Demo</span>
      </div>
    </header>
  );
}
