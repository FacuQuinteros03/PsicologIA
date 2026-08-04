'use client';

import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';

import estilos from './Dialogo.module.css';

export interface PropsDialogo {
  abierto: boolean;
  titulo: string;
  children: ReactNode;
  /** Controles del pie. Normalmente cancelar + la acción principal. */
  acciones: ReactNode;
  onCerrar: () => void;
}

/**
 * Modal sobre el `<dialog>` nativo.
 *
 * Nativo y no un div con overlay: `showModal()` ya atrapa el foco dentro,
 * bloquea el fondo, cierra con Escape y lo anuncia bien a los lectores de
 * pantalla. Replicarlo a mano es mucho código y casi siempre queda peor.
 */
export function Dialogo({ abierto, titulo, children, acciones, onCerrar }: PropsDialogo) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialogo = ref.current;
    if (!dialogo) return;
    if (abierto && !dialogo.open) dialogo.showModal();
    if (!abierto && dialogo.open) dialogo.close();
  }, [abierto]);

  return (
    <dialog
      ref={ref}
      className={estilos.dialogo}
      // Escape dispara `cancel`; se avisa al padre para que sincronice su estado.
      onCancel={(evento) => {
        evento.preventDefault();
        onCerrar();
      }}
      // Click en el fondo: el target es el propio dialog sólo si fue afuera.
      onClick={(evento) => {
        if (evento.target === ref.current) onCerrar();
      }}
    >
      <div className={estilos.contenido}>
        <h2 className={estilos.titulo}>{titulo}</h2>
        <div className={estilos.cuerpo}>{children}</div>
        <div className={estilos.acciones}>{acciones}</div>
      </div>
    </dialog>
  );
}
