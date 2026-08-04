'use client';

import {
  Background,
  BackgroundVariant,
  Controls,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from '@xyflow/react';
import type { Edge, NodeMouseHandler, OnNodeDrag } from '@xyflow/react';
import { useCallback, useEffect } from 'react';

import '@xyflow/react/dist/style.css';

import type { CalidadVinculo, Genograma, TipoVinculo } from '@/lib/types';
import { PersonaNode } from './PersonaNode';
import type { NodoPersona } from './PersonaNode';
import estilos from './GenogramaCanvas.module.css';

/**
 * FUERA del componente a propósito. Si `nodeTypes` se define en el cuerpo, es
 * un objeto nuevo en cada render y React Flow remonta todos los nodos: se
 * pierde la selección y el drag se entrecorta.
 */
const TIPOS_DE_NODO = { persona: PersonaNode };

/** El estilo del vínculo comunica su carga emocional, no sólo su existencia. */
const ESTILO_VINCULO: Record<CalidadVinculo, { stroke: string; strokeWidth: number; strokeDasharray?: string }> = {
  cercano: { stroke: 'var(--exito)', strokeWidth: 2 },
  fusionado: { stroke: 'var(--exito)', strokeWidth: 3.5 },
  distante: { stroke: 'var(--texto-3)', strokeWidth: 1, strokeDasharray: '4 4' },
  conflictivo: { stroke: 'var(--peligro)', strokeWidth: 2 },
  roto: { stroke: 'var(--peligro)', strokeWidth: 1.5, strokeDasharray: '2 5' },
  ambivalente: { stroke: 'var(--alerta)', strokeWidth: 1.5, strokeDasharray: '7 3' },
  neutral: { stroke: 'var(--borde-fuerte)', strokeWidth: 1.5 },
};

const VINCULO_LEGIBLE: Partial<Record<TipoVinculo, string>> = {
  matrimonio: 'matrimonio',
  separacion: 'separación',
  divorcio: 'divorcio',
  pareja: 'pareja',
  amistad: 'amistad',
  laboral: 'laboral',
};

export interface PropsGenogramaCanvas {
  genograma: Genograma;
  /** Se dispara al hacer click en un nodo. `null` al hacer click en el vacío. */
  onSeleccionar?: (nodoId: string | null) => void;
  /** Se dispara al soltar un nodo arrastrado, para persistir la posición. */
  onMover?: (nodoId: string, x: number, y: number) => void;
}

export function GenogramaCanvas({ genograma, onSeleccionar, onMover }: PropsGenogramaCanvas) {
  const [nodos, setNodos, alCambiarNodos] = useNodesState<NodoPersona>(aNodos(genograma));
  const [aristas, setAristas, alCambiarAristas] = useEdgesState<Edge>(aAristas(genograma));

  // Cuando el genograma cambia (por ejemplo, después de procesar notas y crear
  // nodos nuevos), se re-siembra el estado del canvas.
  useEffect(() => {
    setNodos(aNodos(genograma));
    setAristas(aAristas(genograma));
  }, [genograma, setNodos, setAristas]);

  // `OnNodeDrag` y no `NodeMouseHandler`: el drag también llega por touch, así
  // que el evento es MouseEvent | TouchEvent.
  const alSoltarNodo = useCallback<OnNodeDrag<NodoPersona>>(
    (_evento, nodo) => {
      onMover?.(nodo.id, Math.round(nodo.position.x), Math.round(nodo.position.y));
    },
    [onMover],
  );

  const alClickNodo = useCallback<NodeMouseHandler<NodoPersona>>(
    (_evento, nodo) => onSeleccionar?.(nodo.id),
    [onSeleccionar],
  );

  return (
    <div className={estilos.lienzo}>
      <ReactFlow<NodoPersona, Edge>
        nodes={nodos}
        edges={aristas}
        onNodesChange={alCambiarNodos}
        onEdgesChange={alCambiarAristas}
        nodeTypes={TIPOS_DE_NODO}
        onNodeClick={alClickNodo}
        onNodeDragStop={alSoltarNodo}
        onPaneClick={() => onSeleccionar?.(null)}
        fitView
        fitViewOptions={{ padding: 0.25, maxZoom: 1.2 }}
        minZoom={0.3}
        maxZoom={2}
        /* Sin conexión manual en el MVP: los vínculos los crea la IA o el
           formulario. Evita que un drag accidental invente una relación. */
        nodesConnectable={false}
        proOptions={{ hideAttribution: false }}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="var(--borde)" />
        <Controls showInteractive={false} className={estilos.controles} />
      </ReactFlow>
    </div>
  );
}

function aNodos(genograma: Genograma): NodoPersona[] {
  return genograma.nodos.map((nodo) => ({
    id: nodo.id,
    type: 'persona' as const,
    position: { x: nodo.pos_x, y: nodo.pos_y },
    data: {
      etiqueta: nodo.etiqueta,
      nombre: nodo.nombre,
      rol: nodo.rol,
      genero: nodo.genero,
      fallecido: nodo.fallecido,
      esIndice: nodo.es_indice,
    },
  }));
}

function aAristas(genograma: Genograma): Edge[] {
  return genograma.conexiones.map((conexion) => {
    const calidad = conexion.calidad_vinculo ?? 'neutral';
    const etiqueta = conexion.etiqueta ?? VINCULO_LEGIBLE[conexion.tipo_vinculo];

    return {
      id: conexion.id,
      source: conexion.origen_id,
      target: conexion.destino_id,
      type: 'smoothstep',
      style: ESTILO_VINCULO[calidad],
      label: etiqueta,
      labelShowBg: true,
      labelBgPadding: [6, 3] as [number, number],
      labelBgBorderRadius: 3,
      labelBgStyle: { fill: 'var(--superficie)', stroke: 'var(--borde)' },
      labelStyle: { fill: 'var(--texto-2)', fontSize: 11 },
      // Sin `animated`: la marcha de guiones es decoración y distrae en una
      // herramienta que se usa durante una sesión.
      animated: false,
    };
  });
}
