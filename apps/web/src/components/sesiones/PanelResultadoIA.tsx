'use client';

import { Badge, Estado, Tag } from '@/components/ui';
import type { TonoBadge } from '@/components/ui';
import type { NotasEstructuradas, Prioridad } from '@/lib/types';
import estilos from './PanelResultadoIA.module.css';

const TONO_PRIORIDAD: Record<Prioridad, TonoBadge> = {
  alta: 'peligro',
  media: 'alerta',
  baja: 'neutro',
};

export interface PropsPanelResultadoIA {
  resultado: NotasEstructuradas | null;
  cargando?: boolean;
  error?: string | null;
}

/**
 * Salida estructurada del procesamiento de notas.
 *
 * Muestra siempre qué proveedor generó el contenido: `mock` y un modelo real no
 * se pueden confundir en una herramienta clínica.
 */
export function PanelResultadoIA({ resultado, cargando, error }: PropsPanelResultadoIA) {
  if (cargando) {
    return <Estado tipo="cargando" titulo="Procesando notas…" />;
  }

  if (error) {
    return <Estado tipo="error" titulo="No se pudo procesar" detalle={error} />;
  }

  if (!resultado) {
    return (
      <Estado
        titulo="Sin procesar"
        detalle="Escribí las notas y procesalas para obtener el resumen, los temas y las personas mencionadas."
      />
    );
  }

  return (
    <div className={estilos.contenedor}>
      <div className={estilos.procedencia}>
        <Badge tono={resultado.proveedor === 'mock' ? 'alerta' : 'acento'} punto>
          {resultado.proveedor}
        </Badge>
        <span className={estilos.modelo}>{resultado.modelo}</span>
        {resultado.persistido && <Badge tono="exito">guardado</Badge>}
      </div>

      <Seccion titulo="Resumen clínico">
        <p className={estilos.resumen}>{resultado.resumen_clinico}</p>
      </Seccion>

      {resultado.estado_emocional_percibido && (
        <Seccion titulo="Estado emocional percibido">
          <Badge tono="neutro">{resultado.estado_emocional_percibido}</Badge>
        </Seccion>
      )}

      {resultado.tags.length > 0 && (
        <Seccion titulo="Temas" cantidad={resultado.tags.length}>
          <div className={estilos.linea}>
            {resultado.tags.map((t) => (
              <Tag key={t.tag} tag={t.tag} />
            ))}
          </div>
        </Seccion>
      )}

      {resultado.entidades.length > 0 && (
        <Seccion titulo="Personas detectadas" cantidad={resultado.entidades.length}>
          <ul className={estilos.entidades}>
            {resultado.entidades.map((entidad) => (
              <li key={entidad.etiqueta} className={estilos.entidad}>
                <div className={estilos.entidadCabecera}>
                  <span className={estilos.entidadNombre}>{entidad.etiqueta}</span>
                  <Badge tono="neutro">{entidad.rol}</Badge>
                  <Badge tono={entidad.calidad_vinculo === 'conflictivo' ? 'peligro' : 'neutro'}>
                    {entidad.calidad_vinculo}
                  </Badge>
                </div>
                {entidad.contexto && <p className={estilos.contexto}>“{entidad.contexto}”</p>}
              </li>
            ))}
          </ul>
        </Seccion>
      )}

      {resultado.alertas_proxima_sesion.length > 0 && (
        <Seccion titulo="Para la próxima sesión" cantidad={resultado.alertas_proxima_sesion.length}>
          <ul className={estilos.alertas}>
            {resultado.alertas_proxima_sesion.map((alerta, indice) => (
              <li key={`${indice}-${alerta.texto}`} className={estilos.alerta}>
                <Badge tono={TONO_PRIORIDAD[alerta.prioridad]} punto>
                  {alerta.prioridad}
                </Badge>
                <span>{alerta.texto}</span>
              </li>
            ))}
          </ul>
        </Seccion>
      )}
    </div>
  );
}

function Seccion({
  titulo,
  cantidad,
  children,
}: {
  titulo: string;
  cantidad?: number;
  children: React.ReactNode;
}) {
  return (
    <section className={estilos.seccion}>
      <h3 className={estilos.tituloSeccion}>
        {titulo}
        {cantidad !== undefined && <span className={`${estilos.conteo} tabular`}>{cantidad}</span>}
      </h3>
      {children}
    </section>
  );
}
