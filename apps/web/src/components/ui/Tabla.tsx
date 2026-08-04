'use client';

import type { KeyboardEvent, ReactNode } from 'react';

import estilos from './Tabla.module.css';

export interface Columna<T> {
  clave: string;
  encabezado: ReactNode;
  /** Cómo se pinta la celda. Recibe la fila completa. */
  celda: (fila: T) => ReactNode;
  /** Alinea a la derecha y aplica tabular-nums. Para importes, fechas, conteos. */
  numerica?: boolean;
  ancho?: string;
}

export interface PropsTabla<T> {
  columnas: Columna<T>[];
  filas: T[];
  claveDe: (fila: T) => string;
  /** Si viene, cada fila se vuelve navegable con Tab y activable con Enter. */
  onAbrir?: (fila: T) => void;
  /** Controles por fila. Aparecen al hover o foco, con el espacio ya reservado. */
  acciones?: (fila: T) => ReactNode;
  vacio?: ReactNode;
}

/**
 * Tabla compacta y navegable por teclado.
 *
 * Las filas son `tabindex=0` cuando hay `onAbrir`, así se recorren con Tab y se
 * abren con Enter o Espacio sin necesidad de mouse.
 */
export function Tabla<T>({
  columnas,
  filas,
  claveDe,
  onAbrir,
  acciones,
  vacio = 'Sin registros.',
}: PropsTabla<T>) {
  function alPresionar(evento: KeyboardEvent<HTMLTableRowElement>, fila: T) {
    if (!onAbrir) return;
    if (evento.key === 'Enter' || evento.key === ' ') {
      evento.preventDefault();
      onAbrir(fila);
    }
  }

  if (filas.length === 0) {
    return <div className={estilos.vacio}>{vacio}</div>;
  }

  return (
    <div className={estilos.contenedor}>
      <table className={estilos.tabla}>
        <thead>
          <tr>
            {columnas.map((columna) => (
              <th
                key={columna.clave}
                style={columna.ancho ? { width: columna.ancho } : undefined}
                className={columna.numerica ? estilos.derecha : undefined}
                scope="col"
              >
                {columna.encabezado}
              </th>
            ))}
            {acciones && (
              <th className={estilos.acciones} scope="col">
                <span className="sr-only">Acciones</span>
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {filas.map((fila) => (
            <tr
              key={claveDe(fila)}
              className={onAbrir ? estilos.filaInteractiva : undefined}
              tabIndex={onAbrir ? 0 : undefined}
              onClick={onAbrir ? () => onAbrir(fila) : undefined}
              onKeyDown={(evento) => alPresionar(evento, fila)}
            >
              {columnas.map((columna) => (
                <td
                  key={columna.clave}
                  className={
                    columna.numerica ? `${estilos.numerica} ${estilos.derecha}` : undefined
                  }
                >
                  {columna.celda(fila)}
                </td>
              ))}
              {acciones && (
                <td className={estilos.acciones}>
                  <div className={estilos.accionesInternas}>{acciones(fila)}</div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
