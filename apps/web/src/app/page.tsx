'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';

import { Badge, Boton, Estado, Panel, Tabla } from '@/components/ui';
import type { Columna, TonoBadge } from '@/components/ui';
import { api, ErrorAPI } from '@/lib/api';
import { fechaCorta } from '@/lib/formato';
import type { EstadoPaciente, Paciente } from '@/lib/types';
import estilos from './page.module.css';

const TONO_ESTADO: Record<EstadoPaciente, TonoBadge> = {
  activo: 'exito',
  pausa: 'alerta',
  alta: 'acento',
  archivado: 'neutro',
};

export default function PaginaPacientes() {
  const router = useRouter();
  const [pacientes, setPacientes] = useState<Paciente[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Un contador en vez de una función: el botón "Actualizar" lo incrementa y el
  // efecto se vuelve a disparar. Así ningún setState corre de forma síncrona
  // dentro del cuerpo del efecto, que es lo que provoca renders en cascada.
  const [recarga, setRecarga] = useState(0);
  const recargar = useCallback(() => setRecarga((n) => n + 1), []);

  useEffect(() => {
    let vigente = true;
    (async () => {
      try {
        const datos = await api.listarPacientes();
        if (!vigente) return;
        setPacientes(datos);
        setError(null);
      } catch (e) {
        if (vigente) setError(e instanceof ErrorAPI ? e.message : 'Error inesperado.');
      }
    })();
    return () => {
      vigente = false;
    };
  }, [recarga]);

  const columnas: Columna<Paciente>[] = [
    {
      clave: 'nombre',
      encabezado: 'Paciente',
      celda: (p) => (
        <span className={estilos.nombre}>
          {p.apellido}, {p.nombre}
        </span>
      ),
    },
    {
      clave: 'motivo',
      encabezado: 'Motivo de consulta',
      celda: (p) => <span className={estilos.motivo}>{p.motivo_consulta ?? '—'}</span>,
    },
    {
      clave: 'estado',
      encabezado: 'Estado',
      ancho: '110px',
      celda: (p) => (
        <Badge tono={TONO_ESTADO[p.estado]} punto>
          {p.estado}
        </Badge>
      ),
    },
    {
      clave: 'alta',
      encabezado: 'Alta',
      ancho: '110px',
      numerica: true,
      celda: (p) => fechaCorta(p.created_at),
    },
  ];

  return (
    <div className={estilos.pagina}>
      <Panel
        titulo="Pacientes"
        meta={pacientes ? `${pacientes.length}` : undefined}
        acciones={
          <Boton variante="secundario" tamano="sm" onClick={recargar}>
            Actualizar
          </Boton>
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

        {!error && pacientes === null && <Estado tipo="cargando" titulo="Cargando pacientes…" />}

        {!error && pacientes !== null && (
          <Tabla
            columnas={columnas}
            filas={pacientes}
            claveDe={(p) => p.id}
            onAbrir={(p) => router.push(`/pacientes/${p.id}`)}
            acciones={(p) => (
              <Boton
                variante="sutil"
                tamano="sm"
                onClick={(evento) => {
                  evento.stopPropagation();
                  router.push(`/pacientes/${p.id}/sesion`);
                }}
              >
                Nueva sesión
              </Boton>
            )}
            vacio="Todavía no hay pacientes cargados."
          />
        )}
      </Panel>
    </div>
  );
}
