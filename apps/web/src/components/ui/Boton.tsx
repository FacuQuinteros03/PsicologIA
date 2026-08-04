'use client';

import { forwardRef } from 'react';
import type { ButtonHTMLAttributes, ReactNode } from 'react';

import estilos from './Boton.module.css';

export type VarianteBoton = 'primario' | 'secundario' | 'sutil' | 'peligro';
export type TamanoBoton = 'sm' | 'md';

export interface PropsBoton extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** `primario` es el acento; `secundario` es el default con borde. */
  variante?: VarianteBoton;
  tamano?: TamanoBoton;
  /** Se renderiza a la izquierda del texto, en un hueco de ancho fijo. */
  icono?: ReactNode;
  /** Deshabilita y muestra un indicador, SIN cambiar el ancho del botón. */
  cargando?: boolean;
  /** Ocupa todo el ancho disponible. */
  bloque?: boolean;
}

/**
 * Botón base de la app.
 *
 * Para cambiar cómo se ven TODOS los botones, editá `Boton.module.css`.
 * Para cambiar los colores, no toques este archivo: están en
 * `app/globals.css` como variables (`--acento`, `--borde`, etc.).
 *
 * Para agregar una variante nueva: sumá el valor a `VarianteBoton` acá y la
 * clase correspondiente en el `.module.css`. No hace falta nada más.
 */
export const Boton = forwardRef<HTMLButtonElement, PropsBoton>(function Boton(
  {
    variante = 'secundario',
    tamano = 'md',
    icono,
    cargando = false,
    bloque = false,
    disabled,
    className,
    children,
    type = 'button',
    ...resto
  },
  ref,
) {
  const clases = [
    estilos.boton,
    estilos[variante],
    estilos[tamano],
    bloque ? estilos.bloque : '',
    className ?? '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      ref={ref}
      type={type}
      className={clases}
      disabled={disabled || cargando}
      aria-busy={cargando || undefined}
      {...resto}
    >
      {/* El hueco del icono existe siempre que haya icono o carga: así el
          texto no se corre cuando el botón pasa a estado cargando. */}
      {(icono || cargando) && (
        <span className={estilos.icono} aria-hidden="true">
          {cargando ? <span className={estilos.indicador} /> : icono}
        </span>
      )}
      <span className={estilos.etiqueta}>{children}</span>
    </button>
  );
});
