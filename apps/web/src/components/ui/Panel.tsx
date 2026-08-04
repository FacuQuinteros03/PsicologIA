import type { ReactNode } from 'react';

import estilos from './Panel.module.css';

export interface PropsPanel {
  titulo?: ReactNode;
  /** Texto chico a la derecha del título: conteos, estado, timestamps. */
  meta?: ReactNode;
  /** Controles alineados a la derecha del encabezado. */
  acciones?: ReactNode;
  /** Quita el padding del cuerpo. Para tablas y canvas, que van al borde. */
  sinPadding?: boolean;
  /** El cuerpo scrollea y el encabezado queda fijo. Requiere altura del padre. */
  scroll?: boolean;
  children: ReactNode;
  className?: string;
}

/**
 * Contenedor con borde 1px y encabezado opcional. Es la unidad de composición
 * de todas las pantallas: cada zona de la UI vive dentro de un Panel.
 */
export function Panel({
  titulo,
  meta,
  acciones,
  sinPadding = false,
  scroll = false,
  children,
  className,
}: PropsPanel) {
  return (
    <section className={[estilos.panel, className ?? ''].filter(Boolean).join(' ')}>
      {(titulo || acciones) && (
        <header className={estilos.encabezado}>
          <div className={estilos.tituloZona}>
            {titulo && <h2 className={estilos.titulo}>{titulo}</h2>}
            {meta && <span className={`${estilos.meta} tabular`}>{meta}</span>}
          </div>
          {acciones && <div className={estilos.acciones}>{acciones}</div>}
        </header>
      )}
      <div
        className={[
          estilos.cuerpo,
          sinPadding ? estilos.sinPadding : '',
          scroll ? estilos.scroll : '',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        {children}
      </div>
    </section>
  );
}
