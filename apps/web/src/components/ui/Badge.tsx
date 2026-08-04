import type { ReactNode } from 'react';

import estilos from './Badge.module.css';

export type TonoBadge = 'neutro' | 'acento' | 'exito' | 'alerta' | 'peligro';

export interface PropsBadge {
  tono?: TonoBadge;
  /** Punto de color a la izquierda. Ayuda a escanear una columna de estados. */
  punto?: boolean;
  children: ReactNode;
  className?: string;
}

/**
 * Etiqueta de estado. Alto fijo para que una columna de badges no genere
 * saltos de layout cuando cambia el texto.
 */
export function Badge({ tono = 'neutro', punto = false, children, className }: PropsBadge) {
  const clases = [estilos.badge, estilos[tono], className ?? ''].filter(Boolean).join(' ');

  return (
    <span className={clases}>
      {punto && <span className={estilos.punto} aria-hidden="true" />}
      {children}
    </span>
  );
}
