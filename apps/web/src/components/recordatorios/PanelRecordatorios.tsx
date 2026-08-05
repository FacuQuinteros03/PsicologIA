'use client';

import { useState } from 'react';

import { Badge, Boton, Campo, Estado, Select } from '@/components/ui';
import { api, ErrorAPI } from '@/lib/api';
import { fechaCorta } from '@/lib/formato';
import { ETIQUETA_PRIORIDAD, PRIORIDADES } from '@/lib/opciones';
import type { Prioridad, Recordatorio } from '@/lib/types';
import estilos from './PanelRecordatorios.module.css';

const TONO_PRIORIDAD = {
  alta: 'peligro',
  media: 'alerta',
  baja: 'neutro',
} as const;

export interface PropsPanelRecordatorios {
  pacienteId: string;
  recordatorios: Recordatorio[] | null;
  /** Se llama después de cada cambio para que la página recargue la lista. */
  onCambio: () => void;
  /** Mostrar también los ya resueltos. */
  verResueltos: boolean;
  onVerResueltos: (valor: boolean) => void;
}

/**
 * Alertas para la próxima sesión: las que detecta la IA al procesar las notas
 * y las que el terapeuta agrega a mano.
 *
 * Las mutaciones son optimistas sólo en el spinner de la fila que se toca; la
 * lista la recarga la página vía `onCambio`. Así dos filas no pueden quedar
 * desincronizadas entre sí.
 */
export function PanelRecordatorios({
  pacienteId,
  recordatorios,
  onCambio,
  verResueltos,
  onVerResueltos,
}: PropsPanelRecordatorios) {
  const [texto, setTexto] = useState('');
  const [prioridad, setPrioridad] = useState<Prioridad>('media');
  const [guardando, setGuardando] = useState(false);
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function agregar(evento: React.FormEvent) {
    evento.preventDefault();
    const limpio = texto.trim();
    if (!limpio) return;
    setGuardando(true);
    setError(null);
    try {
      await api.crearRecordatorio(pacienteId, { texto: limpio, prioridad });
      setTexto('');
      setPrioridad('media');
      onCambio();
    } catch (e) {
      setError(e instanceof ErrorAPI ? e.message : 'No se pudo agregar.');
    } finally {
      setGuardando(false);
    }
  }

  async function alternar(recordatorio: Recordatorio) {
    setOcupado(recordatorio.id);
    setError(null);
    try {
      await api.actualizarRecordatorio(recordatorio.id, { resuelto: !recordatorio.resuelto });
      onCambio();
    } catch (e) {
      setError(e instanceof ErrorAPI ? e.message : 'No se pudo actualizar.');
    } finally {
      setOcupado(null);
    }
  }

  async function eliminar(recordatorio: Recordatorio) {
    setOcupado(recordatorio.id);
    setError(null);
    try {
      await api.eliminarRecordatorio(recordatorio.id);
      onCambio();
    } catch (e) {
      setError(e instanceof ErrorAPI ? e.message : 'No se pudo eliminar.');
    } finally {
      setOcupado(null);
    }
  }

  return (
    <div className={estilos.contenedor}>
      <form className={estilos.alta} onSubmit={agregar}>
        <Campo
          placeholder="Anotar algo para la próxima sesión…"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          aria-label="Texto del recordatorio"
          maxLength={1000}
          className={estilos.campoTexto}
        />
        <Select
          value={prioridad}
          onChange={(e) => setPrioridad(e.target.value as Prioridad)}
          opciones={PRIORIDADES}
          aria-label="Prioridad"
          className={estilos.campoPrioridad}
        />
        <Boton
          type="submit"
          variante="primario"
          cargando={guardando}
          disabled={texto.trim() === ''}
        >
          Agregar
        </Boton>
      </form>

      {error && (
        <p className={estilos.error} role="alert">
          {error}
        </p>
      )}

      {recordatorios === null ? (
        <Estado tipo="cargando" titulo="Cargando recordatorios…" />
      ) : recordatorios.length === 0 ? (
        <Estado
          tipo="vacio"
          titulo={verResueltos ? 'No hay recordatorios.' : 'Nada pendiente.'}
          detalle={
            verResueltos
              ? 'Ni la IA ni vos anotaron nada todavía.'
              : 'Los que detecte la IA al procesar las notas van a aparecer acá.'
          }
        />
      ) : (
        <ul className={estilos.lista}>
          {recordatorios.map((r) => (
            <li
              key={r.id}
              className={`${estilos.fila} ${r.resuelto ? estilos.filaResuelta : ''}`}
            >
              {/* Checkbox nativo: ya trae foco, Espacio y lectura por lectores
                  de pantalla sin que haya que implementar nada. */}
              <input
                type="checkbox"
                className={estilos.check}
                checked={r.resuelto}
                disabled={ocupado === r.id}
                onChange={() => alternar(r)}
                aria-label={r.resuelto ? `Reabrir: ${r.texto}` : `Marcar hecho: ${r.texto}`}
              />

              <div className={estilos.cuerpo}>
                <span className={estilos.texto}>{r.texto}</span>
                <div className={estilos.meta}>
                  <Badge tono={TONO_PRIORIDAD[r.prioridad]}>
                    {ETIQUETA_PRIORIDAD[r.prioridad]}
                  </Badge>
                  <span className={`${estilos.fecha} tabular`}>
                    {r.resuelto && r.resuelto_at
                      ? `hecho ${fechaCorta(r.resuelto_at)}`
                      : fechaCorta(r.created_at)}
                  </span>
                  {r.sesion_id === null && <span className={estilos.origen}>a mano</span>}
                </div>
              </div>

              <Boton
                variante="sutil"
                tamano="sm"
                onClick={() => eliminar(r)}
                disabled={ocupado === r.id}
                aria-label={`Eliminar: ${r.texto}`}
                className={estilos.borrar}
              >
                Eliminar
              </Boton>
            </li>
          ))}
        </ul>
      )}

      <label className={estilos.verTodos}>
        <input
          type="checkbox"
          checked={verResueltos}
          onChange={(e) => onVerResueltos(e.target.checked)}
        />
        Ver también los resueltos
      </label>
    </div>
  );
}
