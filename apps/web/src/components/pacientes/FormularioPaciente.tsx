'use client';

import { useState } from 'react';
import type { FormEvent } from 'react';

import { AreaTexto, Boton, Campo, Panel, Select } from '@/components/ui';
import { ESTADOS_PACIENTE, FRECUENCIAS, GENEROS, MODALIDADES } from '@/lib/opciones';
import type {
  EstadoPaciente,
  Frecuencia,
  Genero,
  Modalidad,
  PacienteDetalle,
  PacienteNuevo,
} from '@/lib/types';
import estilos from './FormularioPaciente.module.css';

/** Lo que emite el formulario. `estado` sólo viaja en modo edición. */
export type DatosPaciente = PacienteNuevo & { estado?: EstadoPaciente };

/** Estado interno: todo string, que es lo que devuelven los inputs del DOM. */
interface Campos {
  nombre: string;
  apellido: string;
  documento: string;
  fecha_nacimiento: string;
  genero: Genero;
  ocupacion: string;
  email: string;
  telefono: string;
  contacto_emergencia: string;
  telefono_emergencia: string;
  obra_social: string;
  numero_afiliado: string;
  motivo_consulta: string;
  derivado_por: string;
  fecha_inicio: string;
  modalidad: Modalidad;
  frecuencia: Frecuencia;
  honorarios: string;
  notas_administrativas: string;
  estado: EstadoPaciente;
}

const VACIO: Campos = {
  nombre: '', apellido: '', documento: '', fecha_nacimiento: '',
  genero: 'desconocido', ocupacion: '', email: '', telefono: '',
  contacto_emergencia: '', telefono_emergencia: '', obra_social: '',
  numero_afiliado: '', motivo_consulta: '', derivado_por: '',
  fecha_inicio: '', modalidad: 'presencial', frecuencia: 'semanal',
  honorarios: '', notas_administrativas: '', estado: 'activo',
};

function desdePaciente(paciente: PacienteDetalle): Campos {
  return {
    nombre: paciente.nombre,
    apellido: paciente.apellido,
    documento: paciente.documento ?? '',
    fecha_nacimiento: paciente.fecha_nacimiento ?? '',
    genero: paciente.genero,
    ocupacion: paciente.ocupacion ?? '',
    email: paciente.email ?? '',
    telefono: paciente.telefono ?? '',
    contacto_emergencia: paciente.contacto_emergencia ?? '',
    telefono_emergencia: paciente.telefono_emergencia ?? '',
    obra_social: paciente.obra_social ?? '',
    numero_afiliado: paciente.numero_afiliado ?? '',
    motivo_consulta: paciente.motivo_consulta ?? '',
    derivado_por: paciente.derivado_por ?? '',
    fecha_inicio: paciente.fecha_inicio ?? '',
    modalidad: paciente.modalidad,
    frecuencia: paciente.frecuencia,
    honorarios: paciente.honorarios ?? '',
    notas_administrativas: paciente.notas_administrativas ?? '',
    estado: paciente.estado,
  };
}

/** Los campos de texto vacíos viajan como `null`, no como `""`. */
function aPayload(campos: Campos, modoEdicion: boolean): DatosPaciente {
  const opcional = (valor: string) => (valor.trim() === '' ? null : valor.trim());

  const payload: DatosPaciente = {
    nombre: campos.nombre.trim(),
    apellido: campos.apellido.trim(),
    documento: opcional(campos.documento),
    fecha_nacimiento: opcional(campos.fecha_nacimiento),
    genero: campos.genero,
    ocupacion: opcional(campos.ocupacion),
    email: opcional(campos.email),
    telefono: opcional(campos.telefono),
    contacto_emergencia: opcional(campos.contacto_emergencia),
    telefono_emergencia: opcional(campos.telefono_emergencia),
    obra_social: opcional(campos.obra_social),
    numero_afiliado: opcional(campos.numero_afiliado),
    motivo_consulta: opcional(campos.motivo_consulta),
    derivado_por: opcional(campos.derivado_por),
    fecha_inicio: opcional(campos.fecha_inicio),
    modalidad: campos.modalidad,
    frecuencia: campos.frecuencia,
    honorarios: opcional(campos.honorarios),
    notas_administrativas: opcional(campos.notas_administrativas),
  };

  // El estado sólo se edita: al crear, el backend lo pone en `activo`.
  if (modoEdicion) payload.estado = campos.estado;
  return payload;
}

export interface PropsFormularioPaciente {
  /** Si viene, el formulario está en modo edición. */
  inicial?: PacienteDetalle;
  onGuardar: (datos: DatosPaciente) => Promise<void>;
  onCancelar: () => void;
  guardando?: boolean;
  error?: string | null;
}

export function FormularioPaciente({
  inicial,
  onGuardar,
  onCancelar,
  guardando = false,
  error,
}: PropsFormularioPaciente) {
  const modoEdicion = inicial !== undefined;
  const [campos, setCampos] = useState<Campos>(inicial ? desdePaciente(inicial) : VACIO);
  const [tocado, setTocado] = useState(false);

  function set<K extends keyof Campos>(clave: K, valor: Campos[K]) {
    setCampos((previos) => ({ ...previos, [clave]: valor }));
  }

  const faltaNombre = tocado && campos.nombre.trim() === '';
  const faltaApellido = tocado && campos.apellido.trim() === '';

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setTocado(true);
    if (campos.nombre.trim() === '' || campos.apellido.trim() === '') return;
    await onGuardar(aPayload(campos, modoEdicion));
  }

  return (
    <form onSubmit={enviar} className={estilos.formulario} noValidate>
      {error && (
        <p className={estilos.errorGeneral} role="alert">
          {error}
        </p>
      )}

      <Panel titulo="Identificación">
        <div className={estilos.grilla}>
          <Campo
            etiqueta="Nombre *"
            value={campos.nombre}
            onChange={(e) => set('nombre', e.target.value)}
            error={faltaNombre ? 'El nombre es obligatorio.' : undefined}
            autoFocus
            autoComplete="off"
          />
          <Campo
            etiqueta="Apellido *"
            value={campos.apellido}
            onChange={(e) => set('apellido', e.target.value)}
            error={faltaApellido ? 'El apellido es obligatorio.' : undefined}
            autoComplete="off"
          />
          <Campo
            etiqueta="Documento"
            value={campos.documento}
            onChange={(e) => set('documento', e.target.value)}
            ayuda="No puede repetirse entre tus pacientes."
            inputMode="numeric"
            autoComplete="off"
          />
          <Campo
            etiqueta="Fecha de nacimiento"
            type="date"
            value={campos.fecha_nacimiento}
            onChange={(e) => set('fecha_nacimiento', e.target.value)}
          />
          <Select
            etiqueta="Género"
            opciones={GENEROS}
            value={campos.genero}
            onChange={(e) => set('genero', e.target.value as Genero)}
          />
          <Campo
            etiqueta="Ocupación"
            value={campos.ocupacion}
            onChange={(e) => set('ocupacion', e.target.value)}
            autoComplete="off"
          />
        </div>
      </Panel>

      <Panel titulo="Contacto">
        <div className={estilos.grilla}>
          <Campo
            etiqueta="Email"
            type="email"
            value={campos.email}
            onChange={(e) => set('email', e.target.value)}
            autoComplete="off"
          />
          <Campo
            etiqueta="Teléfono"
            type="tel"
            value={campos.telefono}
            onChange={(e) => set('telefono', e.target.value)}
            autoComplete="off"
          />
          <Campo
            etiqueta="Contacto de emergencia"
            value={campos.contacto_emergencia}
            onChange={(e) => set('contacto_emergencia', e.target.value)}
            ayuda="Nombre y vínculo."
            autoComplete="off"
          />
          <Campo
            etiqueta="Teléfono de emergencia"
            type="tel"
            value={campos.telefono_emergencia}
            onChange={(e) => set('telefono_emergencia', e.target.value)}
            autoComplete="off"
          />
        </div>
      </Panel>

      <Panel titulo="Cobertura">
        <div className={estilos.grilla}>
          <Campo
            etiqueta="Obra social o prepaga"
            value={campos.obra_social}
            onChange={(e) => set('obra_social', e.target.value)}
            autoComplete="off"
          />
          <Campo
            etiqueta="Número de afiliado"
            value={campos.numero_afiliado}
            onChange={(e) => set('numero_afiliado', e.target.value)}
            autoComplete="off"
          />
        </div>
      </Panel>

      <Panel titulo="Encuadre del tratamiento">
        <div className={estilos.grilla}>
          <Campo
            etiqueta="Derivado por"
            value={campos.derivado_por}
            onChange={(e) => set('derivado_por', e.target.value)}
            autoComplete="off"
          />
          <Campo
            etiqueta="Inicio del tratamiento"
            type="date"
            value={campos.fecha_inicio}
            onChange={(e) => set('fecha_inicio', e.target.value)}
          />
          <Select
            etiqueta="Modalidad"
            opciones={MODALIDADES}
            value={campos.modalidad}
            onChange={(e) => set('modalidad', e.target.value as Modalidad)}
          />
          <Select
            etiqueta="Frecuencia"
            opciones={FRECUENCIAS}
            value={campos.frecuencia}
            onChange={(e) => set('frecuencia', e.target.value as Frecuencia)}
          />
          <Campo
            etiqueta="Honorarios por sesión"
            type="number"
            min={0}
            step="0.01"
            value={campos.honorarios}
            onChange={(e) => set('honorarios', e.target.value)}
            ayuda="En pesos."
          />
          {modoEdicion && (
            <Select
              etiqueta="Estado"
              opciones={ESTADOS_PACIENTE}
              value={campos.estado}
              onChange={(e) => set('estado', e.target.value as EstadoPaciente)}
              ayuda="Archivar lo saca del listado sin borrar nada."
            />
          )}
        </div>

        <AreaTexto
          etiqueta="Motivo de consulta"
          className={estilos.anchoCompleto}
          value={campos.motivo_consulta}
          onChange={(e) => set('motivo_consulta', e.target.value)}
          rows={3}
          placeholder="Qué trae a la persona a la consulta."
        />
      </Panel>

      <Panel titulo="Administrativo">
        <AreaTexto
          etiqueta="Notas administrativas"
          value={campos.notas_administrativas}
          onChange={(e) => set('notas_administrativas', e.target.value)}
          rows={3}
          ayuda="Facturación, preferencias horarias. Lo clínico va en las sesiones."
        />
      </Panel>

      <div className={estilos.acciones}>
        <Boton variante="sutil" onClick={onCancelar} disabled={guardando}>
          Cancelar
        </Boton>
        <Boton type="submit" variante="primario" cargando={guardando}>
          {modoEdicion ? 'Guardar cambios' : 'Crear paciente'}
        </Boton>
      </div>
    </form>
  );
}
