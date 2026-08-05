/**
 * Etiquetas legibles de los enums del dominio.
 *
 * Los valores crudos vienen del backend en minúscula (`no_binario`,
 * `a_demanda`). Acá viven las traducciones para mostrar, en un solo lugar: si
 * mañana hay que renombrar "Consultante" o traducir la app, se cambia acá y no
 * en cada pantalla.
 */

import type { OpcionSelect } from '@/components/ui';
import type {
  EstadoPaciente,
  Frecuencia,
  Genero,
  Modalidad,
  Prioridad,
  RolNodo,
} from './types';

export const GENEROS: readonly OpcionSelect<Genero>[] = [
  { valor: 'femenino', etiqueta: 'Femenino' },
  { valor: 'masculino', etiqueta: 'Masculino' },
  { valor: 'no_binario', etiqueta: 'No binario' },
  { valor: 'desconocido', etiqueta: 'Prefiere no decirlo' },
];

export const MODALIDADES: readonly OpcionSelect<Modalidad>[] = [
  { valor: 'presencial', etiqueta: 'Presencial' },
  { valor: 'virtual', etiqueta: 'Virtual' },
  { valor: 'mixta', etiqueta: 'Mixta' },
];

export const FRECUENCIAS: readonly OpcionSelect<Frecuencia>[] = [
  { valor: 'semanal', etiqueta: 'Semanal' },
  { valor: 'quincenal', etiqueta: 'Quincenal' },
  { valor: 'mensual', etiqueta: 'Mensual' },
  { valor: 'a_demanda', etiqueta: 'A demanda' },
];

export const ESTADOS_PACIENTE: readonly OpcionSelect<EstadoPaciente>[] = [
  { valor: 'activo', etiqueta: 'En tratamiento' },
  { valor: 'pausa', etiqueta: 'En pausa' },
  { valor: 'alta', etiqueta: 'De alta' },
  { valor: 'archivado', etiqueta: 'Archivado' },
];

export const ETIQUETA_ESTADO: Record<EstadoPaciente, string> = {
  activo: 'En tratamiento',
  pausa: 'En pausa',
  alta: 'De alta',
  archivado: 'Archivado',
};

export const ETIQUETA_MODALIDAD: Record<Modalidad, string> = {
  presencial: 'Presencial',
  virtual: 'Virtual',
  mixta: 'Mixta',
};

export const ETIQUETA_FRECUENCIA: Record<Frecuencia, string> = {
  semanal: 'Semanal',
  quincenal: 'Quincenal',
  mensual: 'Mensual',
  a_demanda: 'A demanda',
};

export const ETIQUETA_GENERO: Record<Genero, string> = {
  femenino: 'Femenino',
  masculino: 'Masculino',
  no_binario: 'No binario',
  desconocido: 'Sin especificar',
};

export const ETIQUETA_ROL: Record<RolNodo, string> = {
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

export const ETIQUETA_PRIORIDAD: Record<Prioridad, string> = {
  alta: 'Alta',
  media: 'Media',
  baja: 'Baja',
};

/** Derivado de las etiquetas: agregar una prioridad nueva actualiza las dos cosas.
 *  El orden es el de urgencia, que es como se lee en un desplegable. */
export const PRIORIDADES: readonly OpcionSelect<Prioridad>[] = (
  ['alta', 'media', 'baja'] as const
).map((valor) => ({ valor, etiqueta: ETIQUETA_PRIORIDAD[valor] }));

/** Formatea un importe como pesos argentinos. */
const PESOS = new Intl.NumberFormat('es-AR', {
  style: 'currency',
  currency: 'ARS',
  maximumFractionDigits: 0,
});

export function honorariosLegibles(valor: string | null): string {
  if (!valor) return '—';
  const numero = Number(valor);
  return Number.isFinite(numero) ? PESOS.format(numero) : '—';
}
