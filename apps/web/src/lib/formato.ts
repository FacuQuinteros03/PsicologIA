/**
 * Formateo de fechas y textos.
 *
 * Todo en es-AR. Los `Intl.DateTimeFormat` se construyen una sola vez a nivel
 * de módulo: crearlos en cada render es sorprendentemente caro en listas largas.
 */

const CORTA = new Intl.DateTimeFormat('es-AR', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
});

const LARGA = new Intl.DateTimeFormat('es-AR', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});

/** `04/08/2026`. Ancho estable, pensado para columnas con tabular-nums. */
export function fechaCorta(iso: string): string {
  return CORTA.format(new Date(iso));
}

/** `04 ago 2026, 16:32`. Para encabezados de detalle. */
export function fechaLarga(iso: string): string {
  return LARGA.format(new Date(iso));
}

/** `hace 3 días`. Cae a la fecha corta cuando pasa más de un mes. */
export function haceCuanto(iso: string): string {
  const dias = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (dias <= 0) return 'hoy';
  if (dias === 1) return 'ayer';
  if (dias < 30) return `hace ${dias} días`;
  return fechaCorta(iso);
}

export function iniciales(nombre: string, apellido: string): string {
  return `${nombre.charAt(0)}${apellido.charAt(0)}`.toUpperCase();
}

/** Corta sin partir palabras al medio. */
export function recortar(texto: string, maximo: number): string {
  if (texto.length <= maximo) return texto;
  const corte = texto.slice(0, maximo);
  const ultimoEspacio = corte.lastIndexOf(' ');
  return `${corte.slice(0, ultimoEspacio > 0 ? ultimoEspacio : maximo)}…`;
}
