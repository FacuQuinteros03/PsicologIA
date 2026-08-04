'use client';

import { useParams, useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { GenogramaCanvas } from '@/components/genograma/GenogramaCanvas';
import { PanelNodo } from '@/components/genograma/PanelNodo';
import { Badge, Boton, Campo, Estado, Panel, Tabla, Tag } from '@/components/ui';
import type { Columna } from '@/components/ui';
import { api, ErrorAPI } from '@/lib/api';
import { fechaCorta, recortar } from '@/lib/formato';
import type {
  Genograma,
  MencionSesion,
  Paciente,
  SesionResumen,
  TagConteo,
} from '@/lib/types';
import estilos from './page.module.css';

export default function PaginaPaciente() {
  const { pacienteId } = useParams<{ pacienteId: string }>();
  const router = useRouter();

  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [genograma, setGenograma] = useState<Genograma | null>(null);
  const [sesiones, setSesiones] = useState<SesionResumen[] | null>(null);
  const [tags, setTags] = useState<TagConteo[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [nodoActivo, setNodoActivo] = useState<string | null>(null);
  const [menciones, setMenciones] = useState<{ nodo: string; lista: MencionSesion[] } | null>(null);

  // Derivadas del estado, no almacenadas: si lo guardado corresponde a otro
  // nodo, todavía estamos cargando el actual.
  const mencionesDelNodo = menciones?.nodo === nodoActivo ? menciones.lista : [];
  const cargandoMenciones = nodoActivo !== null && menciones?.nodo !== nodoActivo;

  const [tagsFiltro, setTagsFiltro] = useState<string[]>([]);
  const [busqueda, setBusqueda] = useState('');

  // --- Carga inicial -------------------------------------------------------
  // Los setState van después del await: hacerlos de forma síncrona en el cuerpo
  // del efecto encadena renders innecesarios.
  useEffect(() => {
    if (!pacienteId) return;
    let vigente = true;
    (async () => {
      try {
        const [p, g, t] = await Promise.all([
          api.obtenerPaciente(pacienteId),
          api.genograma(pacienteId),
          api.nubeDeTags(pacienteId),
        ]);
        if (!vigente) return;
        setPaciente(p);
        setGenograma(g);
        setTags(t);
        setError(null);
      } catch (e) {
        if (vigente) setError(e instanceof ErrorAPI ? e.message : 'Error inesperado.');
      }
    })();
    return () => {
      vigente = false;
    };
  }, [pacienteId]);

  // --- Historial, que se recarga al cambiar los filtros --------------------
  useEffect(() => {
    if (!pacienteId) return;
    let vigente = true;
    api
      .listarSesiones(pacienteId, {
        tags: tagsFiltro.length ? tagsFiltro : undefined,
        q: busqueda.trim() || undefined,
      })
      .then((s) => {
        // Descarta respuestas de una búsqueda ya superada por otra más nueva.
        if (vigente) setSesiones(s);
      })
      .catch((e: ErrorAPI) => vigente && setError(e.message));
    return () => {
      vigente = false;
    };
  }, [pacienteId, tagsFiltro, busqueda]);

  // --- Sesiones del nodo seleccionado --------------------------------------
  // Se guarda junto con el id del nodo que las originó. Así, al cambiar de
  // nodo, la lista vieja se descarta por comparación en vez de por un
  // setState de limpieza dentro del efecto.
  useEffect(() => {
    if (!nodoActivo) return;
    let vigente = true;
    (async () => {
      try {
        const lista = await api.sesionesDelNodo(nodoActivo);
        if (vigente) setMenciones({ nodo: nodoActivo, lista });
      } catch {
        if (vigente) setMenciones({ nodo: nodoActivo, lista: [] });
      }
    })();
    return () => {
      vigente = false;
    };
  }, [nodoActivo]);

  // Escape deselecciona: salir sin tocar el mouse.
  useEffect(() => {
    function alPresionar(evento: KeyboardEvent) {
      if (evento.key === 'Escape') setNodoActivo(null);
    }
    window.addEventListener('keydown', alPresionar);
    return () => window.removeEventListener('keydown', alPresionar);
  }, []);

  const guardarPosicion = useCallback((nodoId: string, x: number, y: number) => {
    // Optimista: el canvas ya movió el nodo, acá sólo se persiste.
    api.moverNodo(nodoId, x, y).catch(() => {
      /* si falla, la posición se recupera al recargar */
    });
  }, []);

  const alternarTag = useCallback((tag: string) => {
    setTagsFiltro((previos) =>
      previos.includes(tag) ? previos.filter((t) => t !== tag) : [...previos, tag],
    );
  }, []);

  const nodoSeleccionado = useMemo(
    () => genograma?.nodos.find((n) => n.id === nodoActivo) ?? null,
    [genograma, nodoActivo],
  );

  const columnas: Columna<SesionResumen>[] = [
    {
      clave: 'fecha',
      encabezado: 'Fecha',
      ancho: '100px',
      numerica: true,
      celda: (s) => fechaCorta(s.fecha_sesion),
    },
    {
      clave: 'resumen',
      encabezado: 'Resumen',
      celda: (s) => (
        <span className={estilos.resumen}>
          {s.resumen_ia ? recortar(s.resumen_ia, 110) : <em className={estilos.pendiente}>Sin procesar</em>}
        </span>
      ),
    },
    {
      clave: 'tags',
      encabezado: 'Temas',
      ancho: '260px',
      celda: (s) => (
        <div className={estilos.tagsFila}>
          {s.tags.slice(0, 3).map((tag) => (
            <Tag key={tag} tag={tag} />
          ))}
          {s.tags.length > 3 && <span className={estilos.mas}>+{s.tags.length - 3}</span>}
        </div>
      ),
    },
    {
      clave: 'estado',
      encabezado: 'IA',
      ancho: '96px',
      celda: (s) =>
        s.ia_estado === 'completado' ? (
          <Badge tono="exito" punto>
            listo
          </Badge>
        ) : s.ia_estado === 'error' ? (
          <Badge tono="peligro" punto>
            error
          </Badge>
        ) : (
          <Badge tono="neutro" punto>
            {s.ia_estado}
          </Badge>
        ),
    },
  ];

  if (error) {
    return (
      <div className={estilos.centro}>
        <Estado
          tipo="error"
          titulo="No se pudo cargar el paciente"
          detalle={error}
          accion={
            <Boton variante="secundario" tamano="sm" onClick={() => router.refresh()}>
              Reintentar
            </Boton>
          }
        />
      </div>
    );
  }

  if (!paciente || !genograma) {
    return (
      <div className={estilos.centro}>
        <Estado tipo="cargando" titulo="Cargando historia clínica…" />
      </div>
    );
  }

  return (
    <div className={estilos.pagina}>
      <div className={estilos.encabezado}>
        <div className={estilos.identidad}>
          <h1 className={estilos.titulo}>
            {paciente.apellido}, {paciente.nombre}
          </h1>
          <Badge tono={paciente.estado === 'activo' ? 'exito' : 'neutro'} punto>
            {paciente.estado}
          </Badge>
        </div>
        {paciente.motivo_consulta && (
          <p className={estilos.motivo}>{paciente.motivo_consulta}</p>
        )}
        <div className={estilos.accionesEncabezado}>
          <Boton
            variante="primario"
            onClick={() => router.push(`/pacientes/${pacienteId}/sesion`)}
          >
            Nueva sesión
          </Boton>
        </div>
      </div>

      <div className={estilos.grilla}>
        <Panel
          className={estilos.panelGenograma}
          titulo="Genograma"
          meta={`${genograma.nodos.length} personas · ${genograma.conexiones.length} vínculos`}
          sinPadding
        >
          <GenogramaCanvas
            genograma={genograma}
            onSeleccionar={setNodoActivo}
            onMover={guardarPosicion}
          />
        </Panel>

        <Panel
          className={estilos.panelLateral}
          titulo={nodoSeleccionado ? 'Persona' : 'Detalle'}
          sinPadding
        >
          <PanelNodo
            nodo={nodoSeleccionado}
            sesiones={mencionesDelNodo}
            cargando={cargandoMenciones}
            onAbrirSesion={(id) => router.push(`/pacientes/${pacienteId}/sesion?sesion=${id}`)}
          />
        </Panel>

        <Panel
          className={estilos.panelHistorial}
          titulo="Historial"
          meta={sesiones ? `${sesiones.length}` : undefined}
          acciones={
            <Campo
              type="search"
              placeholder="Buscar en las notas…"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className={estilos.buscador}
              aria-label="Buscar en el historial"
            />
          }
          sinPadding
        >
          {tags.length > 0 && (
            <div className={estilos.filtros}>
              {tags.map((t) => (
                <Tag
                  key={t.tag}
                  tag={t.tag}
                  cantidad={t.cantidad}
                  activo={tagsFiltro.includes(t.tag)}
                  onSelect={alternarTag}
                />
              ))}
              {tagsFiltro.length > 0 && (
                <Boton variante="sutil" tamano="sm" onClick={() => setTagsFiltro([])}>
                  Limpiar
                </Boton>
              )}
            </div>
          )}

          {sesiones === null ? (
            <Estado tipo="cargando" titulo="Cargando sesiones…" />
          ) : (
            <Tabla
              columnas={columnas}
              filas={sesiones}
              claveDe={(s) => s.id}
              onAbrir={(s) => router.push(`/pacientes/${pacienteId}/sesion?sesion=${s.id}`)}
              vacio={
                tagsFiltro.length || busqueda
                  ? 'Ninguna sesión coincide con el filtro.'
                  : 'Todavía no hay sesiones registradas.'
              }
            />
          )}
        </Panel>
      </div>
    </div>
  );
}
