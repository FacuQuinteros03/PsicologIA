/**
 * Primitivos de UI.
 *
 * Importá siempre desde acá: `import { Boton, Panel } from '@/components/ui'`.
 * Así, si un componente se renombra o se parte en dos, cambia un solo archivo.
 *
 * Para retocar la apariencia, editá el `.module.css` del componente.
 * Para cambiar colores, espaciados o tipografía, editá `app/globals.css`:
 * ningún componente escribe un color literal.
 */

export { Boton } from './Boton';
export type { PropsBoton, TamanoBoton, VarianteBoton } from './Boton';

export { Badge } from './Badge';
export type { PropsBadge, TonoBadge } from './Badge';

export { Tag } from './Tag';
export type { PropsTag } from './Tag';

export { Panel } from './Panel';
export type { PropsPanel } from './Panel';

export { AreaTexto, Campo } from './Campo';
export type { PropsAreaTexto, PropsCampo } from './Campo';

export { Select } from './Select';
export type { OpcionSelect, PropsSelect } from './Select';

export { Tabla } from './Tabla';
export type { Columna, PropsTabla } from './Tabla';

export { Estado } from './Estado';
export type { PropsEstado } from './Estado';

export { Dialogo } from './Dialogo';
export type { PropsDialogo } from './Dialogo';
