/**
 * Cliente HTTP contra la API de FastAPI.
 *
 * Una sola función hace el fetch (`pedir`) y todo lo demás son envoltorios
 * tipados. Así el manejo de errores, la base URL y los headers viven en un
 * único lugar.
 */

import type {
  FiltrosPacientes,
  Genograma,
  MencionSesion,
  NodoGenograma,
  NotasEstructuradas,
  Paciente,
  PacienteCambios,
  PacienteDetalle,
  PacienteNuevo,
  ProcesarNotas,
  Recordatorio,
  RecordatorioCambios,
  RecordatorioNuevo,
  SesionDetalle,
  SesionResumen,
  TagConteo,
} from './types';

const BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') ?? 'http://127.0.0.1:8000';

const V1 = `${BASE}/api/v1`;

/** Error de la API con el status, para poder distinguir un 404 de un 500. */
export class ErrorAPI extends Error {
  constructor(
    public readonly status: number,
    mensaje: string,
  ) {
    super(mensaje);
    this.name = 'ErrorAPI';
  }
}

async function pedir<T>(url: string, init?: RequestInit): Promise<T> {
  let respuesta: Response;
  try {
    respuesta = await fetch(url, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
      cache: 'no-store',
    });
  } catch {
    // fetch sólo rechaza por fallo de red, no por status HTTP.
    throw new ErrorAPI(0, 'No se pudo contactar la API. ¿Está corriendo en el puerto 8000?');
  }

  if (!respuesta.ok) {
    throw new ErrorAPI(respuesta.status, await extraerDetalle(respuesta));
  }

  if (respuesta.status === 204) {
    return undefined as T;
  }
  return (await respuesta.json()) as T;
}

/** FastAPI devuelve `{detail: ...}`; el detail puede ser string o lista. */
async function extraerDetalle(respuesta: Response): Promise<string> {
  try {
    const cuerpo = await respuesta.json();
    const detalle = cuerpo?.detail;
    if (typeof detalle === 'string') return detalle;
    if (Array.isArray(detalle) && detalle.length > 0) {
      return detalle.map((e: { msg?: string }) => e.msg ?? '').join('; ');
    }
  } catch {
    /* el cuerpo no era JSON */
  }
  return `Error ${respuesta.status}`;
}

function conParams(ruta: string, params: Record<string, string | string[] | undefined>): string {
  const busqueda = new URLSearchParams();
  for (const [clave, valor] of Object.entries(params)) {
    if (valor === undefined) continue;
    if (Array.isArray(valor)) {
      valor.forEach((v) => busqueda.append(clave, v));
    } else if (valor !== '') {
      busqueda.set(clave, valor);
    }
  }
  const cadena = busqueda.toString();
  return cadena ? `${ruta}?${cadena}` : ruta;
}

export const api = {
  salud: () => pedir<{ status: string; entorno: string; proveedor_ia: string }>(`${BASE}/health`),

  // --- Pacientes (CRUD) ---
  listarPacientes: (filtros?: FiltrosPacientes) =>
    pedir<Paciente[]>(
      conParams(`${V1}/pacientes`, {
        estado: filtros?.estado,
        q: filtros?.q,
        incluir_archivados: filtros?.incluir_archivados ? 'true' : undefined,
      }),
    ),

  obtenerPaciente: (id: string) => pedir<PacienteDetalle>(`${V1}/pacientes/${id}`),

  crearPaciente: (datos: PacienteNuevo) =>
    pedir<PacienteDetalle>(`${V1}/pacientes`, { method: 'POST', body: JSON.stringify(datos) }),

  actualizarPaciente: (id: string, cambios: PacienteCambios) =>
    pedir<PacienteDetalle>(`${V1}/pacientes/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(cambios),
    }),

  /** Borra al paciente y todo lo que cuelga de él. Irreversible. */
  eliminarPaciente: (id: string) =>
    pedir<void>(`${V1}/pacientes/${id}`, { method: 'DELETE' }),

  /** Baja lógica: lo saca del listado sin destruir la historia clínica. */
  archivarPaciente: (id: string) =>
    pedir<PacienteDetalle>(`${V1}/pacientes/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ estado: 'archivado' }),
    }),

  // --- Historial ---
  listarSesiones: (pacienteId: string, filtros?: { tags?: string[]; q?: string }) =>
    pedir<SesionResumen[]>(
      conParams(`${V1}/pacientes/${pacienteId}/sesiones`, {
        tags: filtros?.tags,
        q: filtros?.q,
      }),
    ),

  nubeDeTags: (pacienteId: string) => pedir<TagConteo[]>(`${V1}/pacientes/${pacienteId}/tags`),

  // --- Recordatorios ---
  recordatorios: (pacienteId: string, soloPendientes = true) =>
    pedir<Recordatorio[]>(
      conParams(`${V1}/pacientes/${pacienteId}/recordatorios`, {
        // Se manda sólo cuando hay que apagar el default del backend, que ya es
        // `true`. `conParams` toma strings, igual que `incluir_archivados`.
        solo_pendientes: soloPendientes ? undefined : 'false',
      }),
    ),

  crearRecordatorio: (pacienteId: string, datos: RecordatorioNuevo) =>
    pedir<Recordatorio>(`${V1}/pacientes/${pacienteId}/recordatorios`, {
      method: 'POST',
      body: JSON.stringify(datos),
    }),

  actualizarRecordatorio: (id: string, cambios: RecordatorioCambios) =>
    pedir<Recordatorio>(`${V1}/recordatorios/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(cambios),
    }),

  eliminarRecordatorio: (id: string) =>
    pedir<void>(`${V1}/recordatorios/${id}`, { method: 'DELETE' }),

  // --- Sesiones ---
  obtenerSesion: (id: string) => pedir<SesionDetalle>(`${V1}/sesiones/${id}`),

  crearSesion: (pacienteId: string, notas = '') =>
    pedir<SesionDetalle>(`${V1}/sesiones`, {
      method: 'POST',
      body: JSON.stringify({ paciente_id: pacienteId, notas_borrador: notas }),
    }),

  guardarBorrador: (sesionId: string, notas: string) =>
    pedir<SesionDetalle>(`${V1}/sesiones/${sesionId}`, {
      method: 'PATCH',
      body: JSON.stringify({ notas_borrador: notas }),
    }),

  procesarNotas: (datos: ProcesarNotas) =>
    pedir<NotasEstructuradas>(`${V1}/sesiones/procesar-notas`, {
      method: 'POST',
      body: JSON.stringify(datos),
    }),

  // --- Genograma ---
  genograma: (pacienteId: string) => pedir<Genograma>(`${V1}/pacientes/${pacienteId}/genograma`),

  sesionesDelNodo: (nodoId: string) =>
    pedir<MencionSesion[]>(`${V1}/genograma/nodos/${nodoId}/sesiones`),

  moverNodo: (nodoId: string, x: number, y: number) =>
    pedir<NodoGenograma>(`${V1}/genograma/nodos/${nodoId}/posicion`, {
      method: 'PATCH',
      body: JSON.stringify({ pos_x: x, pos_y: y }),
    }),
};
