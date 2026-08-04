'use client';

import { useId } from 'react';
import type { InputHTMLAttributes, TextareaHTMLAttributes } from 'react';

import estilos from './Campo.module.css';

interface Base {
  etiqueta?: string;
  /** Texto de ayuda. Ocupa lugar siempre para no mover el layout al aparecer. */
  ayuda?: string;
  error?: string;
  className?: string;
}

export interface PropsCampo extends Base, Omit<InputHTMLAttributes<HTMLInputElement>, 'className'> {}

export interface PropsAreaTexto
  extends Base,
    Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'className'> {}

/** Input de una línea con etiqueta asociada por `id`. */
export function Campo({ etiqueta, ayuda, error, className, ...resto }: PropsCampo) {
  const id = useId();
  const idAyuda = `${id}-ayuda`;

  return (
    <div className={[estilos.grupo, className ?? ''].filter(Boolean).join(' ')}>
      {etiqueta && (
        <label className={estilos.etiqueta} htmlFor={id}>
          {etiqueta}
        </label>
      )}
      <input
        id={id}
        className={`${estilos.control} ${error ? estilos.conError : ''}`}
        aria-invalid={error ? true : undefined}
        aria-describedby={ayuda || error ? idAyuda : undefined}
        {...resto}
      />
      <Pie id={idAyuda} ayuda={ayuda} error={error} />
    </div>
  );
}

/** Textarea. `filas` fija la altura; el editor de notas usa una altura propia. */
export function AreaTexto({ etiqueta, ayuda, error, className, ...resto }: PropsAreaTexto) {
  const id = useId();
  const idAyuda = `${id}-ayuda`;

  return (
    <div className={[estilos.grupo, className ?? ''].filter(Boolean).join(' ')}>
      {etiqueta && (
        <label className={estilos.etiqueta} htmlFor={id}>
          {etiqueta}
        </label>
      )}
      <textarea
        id={id}
        className={`${estilos.control} ${estilos.area} ${error ? estilos.conError : ''}`}
        aria-invalid={error ? true : undefined}
        aria-describedby={ayuda || error ? idAyuda : undefined}
        {...resto}
      />
      <Pie id={idAyuda} ayuda={ayuda} error={error} />
    </div>
  );
}

/** El pie se renderiza siempre que haya ayuda o error, con alto reservado. */
function Pie({ id, ayuda, error }: { id: string; ayuda?: string; error?: string }) {
  if (!ayuda && !error) return null;
  return (
    <p id={id} className={error ? estilos.error : estilos.ayuda} role={error ? 'alert' : undefined}>
      {error ?? ayuda}
    </p>
  );
}
