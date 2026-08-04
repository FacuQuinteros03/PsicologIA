'use client';

import { Badge, Tag } from '@/components/ui';
import type { MencionSesion, NodoGenograma } from '@/lib/types';
import { fechaCorta } from '@/lib/formato';
import estilos from './PanelNodo.module.css';

export interface PropsPanelNodo {
  nodo: NodoGenograma | null;
  sesiones: MencionSesion[];
  cargando?: boolean;
  onAbrirSesion?: (sesionId: string) => void;
}

/**
 * Detalle de la persona seleccionada en el genograma y las sesiones donde
 * aparece. Es la contracara del click en el nodo.
 */
export function PanelNodo({ nodo, sesiones, cargando = false, onAbrirSesion }: PropsPanelNodo) {
  if (!nodo) {
    return (
      <div className={estilos.vacio}>
        <p>Seleccioná una persona del genograma.</p>
        <p className={estilos.pista}>Vas a ver acá las sesiones donde aparece.</p>
      </div>
    );
  }

  return (
    <div className={estilos.contenedor}>
      <header className={estilos.ficha}>
        <div className={estilos.identidad}>
          <span className={estilos.etiqueta}>{nodo.etiqueta}</span>
          {nodo.es_indice && <Badge tono="acento">consultante</Badge>}
          {nodo.fallecido && <Badge tono="neutro">fallecido</Badge>}
        </div>
        {nodo.nombre && nodo.nombre !== nodo.etiqueta && (
          <p className={estilos.nombre}>{nodo.nombre}</p>
        )}
        <dl className={estilos.datos}>
          <div>
            <dt>Rol</dt>
            <dd>{nodo.rol}</dd>
          </div>
          <div>
            <dt>Género</dt>
            <dd>{nodo.genero.replace('_', ' ')}</dd>
          </div>
          <div>
            <dt>Menciones</dt>
            <dd className="tabular">{sesiones.reduce((t, s) => t + s.menciones, 0)}</dd>
          </div>
        </dl>
        {nodo.notas && <p className={estilos.notas}>{nodo.notas}</p>}
      </header>

      <div className={estilos.listado}>
        <h3 className={estilos.subtitulo}>
          Sesiones donde aparece
          <span className={`${estilos.conteo} tabular`}>{sesiones.length}</span>
        </h3>

        {cargando && <p className={estilos.estado}>Cargando…</p>}

        {!cargando && sesiones.length === 0 && (
          <p className={estilos.estado}>Todavía no aparece en ninguna sesión registrada.</p>
        )}

        <ul className={estilos.sesiones}>
          {sesiones.map((sesion) => (
            <li key={sesion.sesion_id}>
              <button
                type="button"
                className={estilos.sesion}
                onClick={() => onAbrirSesion?.(sesion.sesion_id)}
              >
                <div className={estilos.sesionCabecera}>
                  <span className={`${estilos.fecha} tabular`}>
                    {fechaCorta(sesion.fecha_sesion)}
                  </span>
                  {sesion.menciones > 1 && (
                    <Badge tono="neutro">{sesion.menciones} menciones</Badge>
                  )}
                </div>

                {sesion.contexto && <p className={estilos.contexto}>“{sesion.contexto}”</p>}

                {sesion.tags.length > 0 && (
                  <div className={estilos.tags}>
                    {sesion.tags.slice(0, 4).map((tag) => (
                      <Tag key={tag} tag={tag} />
                    ))}
                  </div>
                )}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
