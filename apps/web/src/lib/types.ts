/**
 * Espejo de los schemas Pydantic del backend (`apps/api/app/schemas/`).
 *
 * Se mantiene a mano y no generado: son pocos tipos y el costo de sincronizar
 * es menor que el de sumar un paso de codegen al build. Si cambia un schema en
 * el backend, se cambia acá. El contrato real está en `/docs` de la API.
 */

// --- Enums (los valores coinciden exactamente con los del backend) ----------

export type EstadoPaciente = 'activo' | 'pausa' | 'alta' | 'archivado';

export type EstadoIA = 'pendiente' | 'procesando' | 'completado' | 'error';

export type Prioridad = 'baja' | 'media' | 'alta';

export type RolNodo =
  | 'indice'
  | 'madre'
  | 'padre'
  | 'hermano'
  | 'pareja'
  | 'hijo'
  | 'abuelo'
  | 'tio'
  | 'amigo'
  | 'laboral'
  | 'terapeuta'
  | 'otro';

export type Genero = 'femenino' | 'masculino' | 'no_binario' | 'desconocido';

export type TipoVinculo =
  | 'filial'
  | 'parental'
  | 'pareja'
  | 'matrimonio'
  | 'separacion'
  | 'divorcio'
  | 'hermano'
  | 'amistad'
  | 'laboral'
  | 'otro';

export type CalidadVinculo =
  | 'cercano'
  | 'distante'
  | 'conflictivo'
  | 'fusionado'
  | 'roto'
  | 'ambivalente'
  | 'neutral';

// --- Pacientes --------------------------------------------------------------

export interface Paciente {
  id: string;
  nombre: string;
  apellido: string;
  fecha_nacimiento: string | null;
  email: string | null;
  telefono: string | null;
  motivo_consulta: string | null;
  estado: EstadoPaciente;
  created_at: string;
}

export interface PacienteNuevo {
  nombre: string;
  apellido: string;
  fecha_nacimiento?: string | null;
  email?: string | null;
  telefono?: string | null;
  motivo_consulta?: string | null;
}

export interface Recordatorio {
  id: string;
  sesion_id: string;
  texto: string;
  prioridad: Prioridad;
  resuelto: boolean;
  created_at: string;
}

// --- Sesiones ---------------------------------------------------------------

export interface SesionResumen {
  id: string;
  fecha_sesion: string;
  numero_sesion: number | null;
  resumen_ia: string | null;
  tags: string[];
  estado_emocional: string | null;
  ia_estado: EstadoIA;
}

export interface SesionDetalle extends SesionResumen {
  paciente_id: string;
  notas_borrador: string;
  ia_modelo: string | null;
  ia_procesado_at: string | null;
}

export interface TagConteo {
  tag: string;
  cantidad: number;
}

// --- Genograma --------------------------------------------------------------

export interface NodoGenograma {
  id: string;
  etiqueta: string;
  nombre: string | null;
  rol: RolNodo;
  genero: Genero;
  fecha_nacimiento: string | null;
  fallecido: boolean;
  pos_x: number;
  pos_y: number;
  notas: string | null;
  es_indice: boolean;
}

export interface ConexionGenograma {
  id: string;
  origen_id: string;
  destino_id: string;
  tipo_vinculo: TipoVinculo;
  calidad_vinculo: CalidadVinculo | null;
  etiqueta: string | null;
}

export interface Genograma {
  paciente_id: string;
  nodos: NodoGenograma[];
  conexiones: ConexionGenograma[];
}

/** Una sesión donde aparece un nodo. Alimenta el panel lateral del canvas. */
export interface MencionSesion {
  sesion_id: string;
  fecha_sesion: string;
  menciones: number;
  contexto: string | null;
  resumen_ia: string | null;
  tags: string[];
}

// --- Procesamiento con IA ---------------------------------------------------

export interface TagIA {
  tag: string;
  relevancia: number;
}

export interface EntidadIA {
  etiqueta: string;
  nombre: string;
  rol: RolNodo;
  genero: Genero;
  contexto: string;
  vinculo_con_paciente: TipoVinculo;
  calidad_vinculo: CalidadVinculo;
}

export interface AlertaIA {
  texto: string;
  prioridad: Prioridad;
}

export interface NotasEstructuradas {
  resumen_clinico: string;
  temas_principales: string[];
  tags: TagIA[];
  entidades: EntidadIA[];
  alertas_proxima_sesion: AlertaIA[];
  estado_emocional_percibido: string;
  proveedor: string;
  modelo: string;
  procesado_en: string;
  sesion_id: string | null;
  persistido: boolean;
}

export interface ProcesarNotas {
  notas: string;
  paciente_id?: string;
  sesion_id?: string;
  persistir?: boolean;
}
