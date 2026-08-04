import type { ReactNode } from 'react';

import estilos from './Estado.module.css';

export interface PropsEstado {
  tipo?: 'cargando' | 'error' | 'vacio';
  titulo: string;
  detalle?: ReactNode;
  accion?: ReactNode;
}

/**
 * Estado de carga, error o lista vacía.
 *
 * Existe para que las tres situaciones se vean igual en toda la app y no se
 * resuelvan con un `<p>Cargando...</p>` distinto en cada pantalla.
 */
export function Estado({ tipo = 'vacio', titulo, detalle, accion }: PropsEstado) {
  return (
    <div className={estilos.caja} role={tipo === 'error' ? 'alert' : 'status'}>
      {tipo === 'cargando' && <span className={estilos.indicador} aria-hidden="true" />}
      <p className={tipo === 'error' ? estilos.tituloError : estilos.titulo}>{titulo}</p>
      {detalle && <p className={estilos.detalle}>{detalle}</p>}
      {accion && <div className={estilos.accion}>{accion}</div>}
    </div>
  );
}
