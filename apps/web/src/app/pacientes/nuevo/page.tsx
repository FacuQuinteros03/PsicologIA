'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { FormularioPaciente } from '@/components/pacientes/FormularioPaciente';
import type { DatosPaciente } from '@/components/pacientes/FormularioPaciente';
import { api, ErrorAPI } from '@/lib/api';
import estilos from '../formulario.module.css';

export default function PaginaNuevoPaciente() {
  const router = useRouter();
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function guardar(datos: DatosPaciente) {
    setGuardando(true);
    setError(null);
    try {
      const creado = await api.crearPaciente(datos);
      // Directo a su ficha: el flujo natural después de dar de alta es empezar
      // a trabajar con esa persona, no volver al listado.
      router.push(`/pacientes/${creado.id}`);
    } catch (e) {
      setError(e instanceof ErrorAPI ? e.message : 'No se pudo crear el paciente.');
      setGuardando(false);
    }
  }

  return (
    <div className={estilos.pagina}>
      <header className={estilos.encabezado}>
        <h1 className={estilos.titulo}>Nuevo paciente</h1>
        <p className={estilos.ayuda}>
          Sólo nombre y apellido son obligatorios. El resto se puede completar después.
        </p>
      </header>

      <FormularioPaciente
        onGuardar={guardar}
        onCancelar={() => router.push('/')}
        guardando={guardando}
        error={error}
      />
    </div>
  );
}
