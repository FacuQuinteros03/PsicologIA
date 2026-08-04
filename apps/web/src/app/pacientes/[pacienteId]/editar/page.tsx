'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { FormularioPaciente } from '@/components/pacientes/FormularioPaciente';
import type { DatosPaciente } from '@/components/pacientes/FormularioPaciente';
import { Boton, Estado } from '@/components/ui';
import { api, ErrorAPI } from '@/lib/api';
import type { PacienteDetalle } from '@/lib/types';
import estilos from '../../formulario.module.css';

export default function PaginaEditarPaciente() {
  const { pacienteId } = useParams<{ pacienteId: string }>();
  const router = useRouter();

  const [paciente, setPaciente] = useState<PacienteDetalle | null>(null);
  const [errorCarga, setErrorCarga] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!pacienteId) return;
    let vigente = true;
    (async () => {
      try {
        const datos = await api.obtenerPaciente(pacienteId);
        if (vigente) setPaciente(datos);
      } catch (e) {
        if (vigente) setErrorCarga(e instanceof ErrorAPI ? e.message : 'Error inesperado.');
      }
    })();
    return () => {
      vigente = false;
    };
  }, [pacienteId]);

  async function guardar(datos: DatosPaciente) {
    setGuardando(true);
    setError(null);
    try {
      await api.actualizarPaciente(pacienteId, datos);
      router.push(`/pacientes/${pacienteId}`);
    } catch (e) {
      setError(e instanceof ErrorAPI ? e.message : 'No se pudieron guardar los cambios.');
      setGuardando(false);
    }
  }

  if (errorCarga) {
    return (
      <div className={estilos.centro}>
        <Estado
          tipo="error"
          titulo="No se pudo cargar la ficha"
          detalle={errorCarga}
          accion={
            <Boton variante="secundario" tamano="sm" onClick={() => router.push('/')}>
              Volver al listado
            </Boton>
          }
        />
      </div>
    );
  }

  if (!paciente) {
    return (
      <div className={estilos.centro}>
        <Estado tipo="cargando" titulo="Cargando ficha…" />
      </div>
    );
  }

  return (
    <div className={estilos.pagina}>
      <header className={estilos.encabezado}>
        <h1 className={estilos.titulo}>
          Editar · {paciente.apellido}, {paciente.nombre}
        </h1>
        <p className={estilos.ayuda}>
          Los cambios se aplican sobre la ficha; la historia clínica no se toca.
        </p>
      </header>

      <FormularioPaciente
        inicial={paciente}
        onGuardar={guardar}
        onCancelar={() => router.push(`/pacientes/${pacienteId}`)}
        guardando={guardando}
        error={error}
      />
    </div>
  );
}
