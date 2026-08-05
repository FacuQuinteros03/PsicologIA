"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  Badge,
  Boton,
  Campo,
  Dialogo,
  Estado,
  Panel,
  Select,
  Tabla,
} from "@/components/ui";
import type { Columna, TonoBadge } from "@/components/ui";
import { api, ErrorAPI } from "@/lib/api";
import { fechaCorta } from "@/lib/formato";
import {
  ESTADOS_PACIENTE,
  ETIQUETA_ESTADO,
  ETIQUETA_MODALIDAD,
} from "@/lib/opciones";
import type { EstadoPaciente, Paciente } from "@/lib/types";
import estilos from "./page.module.css";

const TONO_ESTADO: Record<EstadoPaciente, TonoBadge> = {
  activo: "exito",
  pausa: "alerta",
  alta: "acento",
  archivado: "neutro",
};

export default function PaginaPacientes() {
  const router = useRouter();

  const [pacientes, setPacientes] = useState<Paciente[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [recarga, setRecarga] = useState(0);

  const [busqueda, setBusqueda] = useState("");
  const [estado, setEstado] = useState<EstadoPaciente | "">("");

  const [aBorrar, setABorrar] = useState<Paciente | null>(null);
  const [borrando, setBorrando] = useState(false);

  const recargar = useCallback(() => setRecarga((n) => n + 1), []);

  useEffect(() => {
    let vigente = true;
    (async () => {
      try {
        const datos = await api.listarPacientes({
          q: busqueda.trim() || undefined,
          estado: estado || undefined,
          incluir_archivados: estado === "archivado",
        });
        if (!vigente) return;
        setPacientes(datos);
        setError(null);
      } catch (e) {
        if (vigente)
          setError(e instanceof ErrorAPI ? e.message : "Error inesperado.");
      }
    })();
    return () => {
      vigente = false;
    };
  }, [recarga, busqueda, estado]);

  async function confirmarBorrado() {
    if (!aBorrar) return;
    setBorrando(true);
    try {
      await api.eliminarPaciente(aBorrar.id);
      setABorrar(null);
      recargar();
    } catch (e) {
      setError(e instanceof ErrorAPI ? e.message : "No se pudo eliminar.");
    } finally {
      setBorrando(false);
    }
  }

  async function archivar(paciente: Paciente) {
    try {
      await api.archivarPaciente(paciente.id);
      recargar();
    } catch (e) {
      setError(e instanceof ErrorAPI ? e.message : "No se pudo archivar.");
    }
  }

  const columnas: Columna<Paciente>[] = [
    {
      clave: "nombre",
      encabezado: "Paciente",
      celda: (p) => (
        <div className={estilos.celdaNombre}>
          <span className={estilos.nombre}>
            {p.apellido}, {p.nombre}
          </span>
          {p.documento && (
            <span className={`${estilos.documento} tabular`}>
              {p.documento}
            </span>
          )}
        </div>
      ),
    },
    {
      clave: "edad",
      encabezado: "Edad",
      ancho: "70px",
      numerica: true,
      celda: (p) => (p.edad !== null ? p.edad : "—"),
    },
    {
      clave: "motivo",
      encabezado: "Motivo de consulta",
      celda: (p) => (
        <span className={estilos.motivo}>{p.motivo_consulta ?? "—"}</span>
      ),
    },
    {
      clave: "modalidad",
      encabezado: "Modalidad",
      ancho: "110px",
      celda: (p) => (
        <span className={estilos.tenue}>{ETIQUETA_MODALIDAD[p.modalidad]}</span>
      ),
    },
    {
      clave: "estado",
      encabezado: "Estado",
      ancho: "140px",
      celda: (p) => (
        <Badge tono={TONO_ESTADO[p.estado]} punto>
          {ETIQUETA_ESTADO[p.estado]}
        </Badge>
      ),
    },
    {
      clave: "alta",
      encabezado: "Alta",
      ancho: "100px",
      numerica: true,
      celda: (p) => fechaCorta(p.created_at),
    },
  ];

  return (
    <div className={estilos.pagina}>
      {/* Banner de Bienvenida / Mindful Space (Estilo Notion Card) */}
      <section className={estilos.heroNotion}>
        <div className={estilos.heroContenido}>
          <span className={estilos.heroEtiqueta}>🌱 Espacio Clínico</span>
          <h1 className={estilos.heroTitulo}>
            Historias Clínicas y Acompañamiento
          </h1>
          <p className={estilos.heroBajada}>
            Gestioná tus pacientes, revisá notas asistidas por IA y organizá el
            espacio terapéutico con tranquilidad.
          </p>
        </div>
      </section>

      <Panel
        titulo="Pacientes"
        meta={pacientes ? `${pacientes.length}` : undefined}
        acciones={
          <div className={estilos.busquedaYFiltros}>
            <Campo
              type="search"
              placeholder="Buscar por nombre o DNI…"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className={estilos.buscador}
              aria-label="Buscar pacientes"
            />
            <Select
              opciones={ESTADOS_PACIENTE}
              placeholder="Todos los estados"
              value={estado}
              onChange={(e) => setEstado(e.target.value as EstadoPaciente | "")}
              className={estilos.filtroEstado}
              aria-label="Filtrar por estado"
            />
            <Boton
              variante="primario"
              tamano="sm"
              onClick={() => router.push("/pacientes/nuevo")}
            >
              Nuevo paciente
            </Boton>
          </div>
        }
        sinPadding
      >
        {error && (
          <Estado
            tipo="error"
            titulo="No se pudo cargar la lista"
            detalle={error}
            accion={
              <Boton variante="secundario" tamano="sm" onClick={recargar}>
                Reintentar
              </Boton>
            }
          />
        )}

        {!error && pacientes === null && (
          <Estado tipo="cargando" titulo="Cargando pacientes…" />
        )}

        {!error && pacientes !== null && (
          <Tabla
            columnas={columnas}
            filas={pacientes}
            claveDe={(p) => p.id}
            onAbrir={(p) => router.push(`/pacientes/${p.id}`)}
            acciones={(p) => (
              <>
                <Boton
                  variante="sutil"
                  tamano="sm"
                  onClick={(evento) => {
                    evento.stopPropagation();
                    router.push(`/pacientes/${p.id}/editar`);
                  }}
                >
                  Editar
                </Boton>
                {p.estado !== "archivado" && (
                  <Boton
                    variante="sutil"
                    tamano="sm"
                    onClick={(evento) => {
                      evento.stopPropagation();
                      archivar(p);
                    }}
                  >
                    Archivar
                  </Boton>
                )}
                <Boton
                  variante="sutil"
                  tamano="sm"
                  onClick={(evento) => {
                    evento.stopPropagation();
                    setABorrar(p);
                  }}
                >
                  Eliminar
                </Boton>
              </>
            )}
            vacio={
              busqueda || estado
                ? "Ningún paciente coincide con el filtro."
                : "Todavía no hay pacientes cargados."
            }
          />
        )}
      </Panel>

      <Dialogo
        abierto={aBorrar !== null}
        titulo="Eliminar paciente"
        onCerrar={() => setABorrar(null)}
        acciones={
          <>
            <Boton
              variante="sutil"
              onClick={() => setABorrar(null)}
              disabled={borrando}
            >
              Cancelar
            </Boton>
            <Boton
              variante="peligro"
              onClick={confirmarBorrado}
              cargando={borrando}
            >
              Eliminar definitivamente
            </Boton>
          </>
        }
      >
        <p>
          Se va a borrar a{" "}
          <strong>
            {aBorrar?.apellido}, {aBorrar?.nombre}
          </strong>{" "}
          junto con{" "}
          <strong>todas sus sesiones, su genograma y sus recordatorios</strong>.
          La acción no se puede deshacer.
        </p>
        <p className={estilos.sugerencia}>
          💡 <strong>Recomendación:</strong> Si sólo querés sacarlo de tu vista
          diaria, usá <strong>Archivar</strong>. Esto conserva la historia
          clínica respetando los requisitos legales sin recargar tu lista.
        </p>
      </Dialogo>
    </div>
  );
}
