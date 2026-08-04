'use client';

import { Handle, Position } from '@xyflow/react';
import type { Node, NodeProps } from '@xyflow/react';

import type { Genero, RolNodo } from '@/lib/types';
import estilos from './PersonaNode.module.css';

/**
 * `type` y no `interface`: React Flow exige que los datos del nodo sean
 * asignables a `Record<string, unknown>`, y las interfaces no lo satisfacen.
 */
export type DatosPersona = {
  etiqueta: string;
  nombre: string | null;
  rol: RolNodo;
  genero: Genero;
  fallecido: boolean;
  esIndice: boolean;
};

export type NodoPersona = Node<DatosPersona, 'persona'>;

/** Forma según la convención de genogramas. */
const FORMA: Record<Genero, string> = {
  masculino: estilos.cuadrado,
  femenino: estilos.circulo,
  no_binario: estilos.hexagono,
  desconocido: estilos.rombo,
};

const ROL_LEGIBLE: Record<RolNodo, string> = {
  indice: 'Consultante',
  madre: 'Madre',
  padre: 'Padre',
  hermano: 'Hermano/a',
  pareja: 'Pareja',
  hijo: 'Hijo/a',
  abuelo: 'Abuelo/a',
  tio: 'Tío/a',
  amigo: 'Amistad',
  laboral: 'Laboral',
  terapeuta: 'Terapeuta',
  otro: 'Otro',
};

export function PersonaNode({ data, selected }: NodeProps<NodoPersona>) {
  const clases = [
    estilos.figura,
    FORMA[data.genero],
    data.esIndice ? estilos.indice : '',
    data.fallecido ? estilos.fallecido : '',
    selected ? estilos.seleccionado : '',
  ]
    .filter(Boolean)
    .join(' ');

  const descripcion = [
    data.nombre ?? data.etiqueta,
    ROL_LEGIBLE[data.rol],
    data.fallecido ? 'fallecido' : null,
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <div className={estilos.nodo}>
      {/* Handles en los cuatro lados para que los vínculos salgan por donde
          quede mejor. Sin `Handle` el edge no se puede anclar. */}
      <Handle type="target" position={Position.Top} className={estilos.puerto} />
      <Handle type="source" position={Position.Bottom} className={estilos.puerto} />
      <Handle type="target" position={Position.Left} id="izq" className={estilos.puerto} />
      <Handle type="source" position={Position.Right} id="der" className={estilos.puerto} />

      <div className={clases} aria-hidden="true">
        {data.fallecido && <span className={estilos.cruz} />}
      </div>

      <div className={estilos.textos}>
        <span className={estilos.etiqueta} title={descripcion}>
          {data.etiqueta}
        </span>
        <span className={estilos.rol}>{ROL_LEGIBLE[data.rol]}</span>
      </div>
    </div>
  );
}
