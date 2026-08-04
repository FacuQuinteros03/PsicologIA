'use client';

import { useId } from 'react';
import type { SelectHTMLAttributes } from 'react';

import estilos from './Select.module.css';

export interface OpcionSelect<T extends string = string> {
  valor: T;
  etiqueta: string;
}

export interface PropsSelect<T extends string = string>
  extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'className' | 'children'> {
  etiqueta?: string;
  opciones: readonly OpcionSelect<T>[];
  ayuda?: string;
  error?: string;
  /** Opción vacía inicial, para campos no obligatorios. */
  placeholder?: string;
  className?: string;
}

/**
 * Select nativo.
 *
 * Nativo a propósito y no un dropdown propio: el del sistema ya trae navegación
 * por teclado, búsqueda al tipear y comportamiento correcto en móvil. Un
 * reemplazo hecho a mano tendría que reimplementar todo eso, y casi siempre peor.
 */
export function Select<T extends string = string>({
  etiqueta,
  opciones,
  ayuda,
  error,
  placeholder,
  className,
  ...resto
}: PropsSelect<T>) {
  const id = useId();
  const idAyuda = `${id}-ayuda`;

  return (
    <div className={[estilos.grupo, className ?? ''].filter(Boolean).join(' ')}>
      {etiqueta && (
        <label className={estilos.etiqueta} htmlFor={id}>
          {etiqueta}
        </label>
      )}
      <div className={estilos.envoltorio}>
        <select
          id={id}
          className={`${estilos.control} ${error ? estilos.conError : ''}`}
          aria-invalid={error ? true : undefined}
          aria-describedby={ayuda || error ? idAyuda : undefined}
          {...resto}
        >
          {placeholder && <option value="">{placeholder}</option>}
          {opciones.map((opcion) => (
            <option key={opcion.valor} value={opcion.valor}>
              {opcion.etiqueta}
            </option>
          ))}
        </select>
        <span className={estilos.flecha} aria-hidden="true" />
      </div>
      {(ayuda || error) && (
        <p id={idAyuda} className={error ? estilos.error : estilos.ayuda} role={error ? 'alert' : undefined}>
          {error ?? ayuda}
        </p>
      )}
    </div>
  );
}
