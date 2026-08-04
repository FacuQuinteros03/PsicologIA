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

export type Modalidad = 'presencial' | 'virtual' | 'mixta';

export type Frecuencia = 'semanal' | 'quincenal' | 'mensual' | 'a_demanda';

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

/** Fila del listado. Es lo que devuelve `GET /pacientes`. */
export interface Paciente {
  id: string;
  nombre: string;
  apellido: string;
  documento: string | null;
  fecha_nacimiento: string | null;
  /** La calcula el backend; no se guarda. */
  edad: number | null;
  genero: Genero;
  email: string | null;
  telefono: string | null;
  motivo_consulta: string | null;
  estado: EstadoPaciente;
  modalidad: Modalidad;
  frecuencia: Frecuencia;
  created_at: string;
}

/** Ficha completa. La devuelven GET por id, POST y PATCH. */
export interface PacienteDetalle extends Paciente {
  ocupacion: string | null;
  contacto_emergencia: string | null;
  telefono_emergencia: string | null;
  obra_social: string | null;
  numero_afiliado: string | null;
  derivado_por: string | null;
  fecha_inicio: string | null;
  honorarios: string | null;
  notas_administrativas: string | null;
  updated_at: string;
  total_sesiones: number;
  total_nodos: number;
  recordatorios_pendientes: number;
}

/** Payload de alta. `estado` no va: todo paciente nuevo nace activo. */
export interface PacienteNuevo {
  nombre: string;
  apellido: string;
  documento?: string | null;
  fecha_nacimiento?: string | null;
  genero?: Genero;
  ocupacion?: string | null;
  email?: string | null;
  telefono?: string | null;
  contacto_emergencia?: string | null;
  telefono_emergencia?: string | null;
  obra_social?: string | null;
  numero_afiliado?: string | null;
  motivo_consulta?: string | null;
  derivado_por?: string | null;
  fecha_inicio?: string | null;
  modalidad?: Modalidad;
  frecuencia?: Frecuencia;
  honorarios?: string | null;
  notas_administrativas?: string | null;
}

/**
 * Payload de edición. Todo opcional, semántica PATCH: lo que no se manda queda
 * intacto y lo que se manda en `null` se borra.
 */
export type PacienteCambios = Partial<PacienteNuevo> & { estado?: EstadoPaciente };

export interface FiltrosPacientes {
  estado?: EstadoPaciente;
  q?: string;
  incluir_archivados?: boolean;
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
