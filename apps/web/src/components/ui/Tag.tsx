'use client';

import estilos from './Tag.module.css';

export interface PropsTag {
  /** El slug sin `#`. El numeral lo agrega el componente. */
  tag: string;
  /** Frecuencia del tag. Se alinea con tabular-nums entre filas. */
  cantidad?: number;
  /** Sólo aplica cuando hay `onSelect`. */
  activo?: boolean;
  /** Si viene, el tag se comporta como un toggle de filtro y es focusable. */
  onSelect?: (tag: string) => void;
}

/**
 * Etiqueta temática de una sesión.
 *
 * Sin `onSelect` es un `<span>` decorativo; con `onSelect` es un `<button>`
 * con `aria-pressed`, navegable por teclado como cualquier control.
 */
export function Tag({ tag, cantidad, activo = false, onSelect }: PropsTag) {
  const contenido = (
    <>
      <span className={estilos.numeral} aria-hidden="true">
        #
      </span>
      {tag}
      {cantidad !== undefined && (
        <span className={`${estilos.cantidad} tabular`}>{cantidad}</span>
      )}
    </>
  );

  if (!onSelect) {
    return <span className={estilos.tag}>{contenido}</span>;
  }

  return (
    <button
      type="button"
      className={`${estilos.tag} ${estilos.interactivo} ${activo ? estilos.activo : ''}`}
      aria-pressed={activo}
      onClick={() => onSelect(tag)}
    >
      {contenido}
    </button>
  );
}
