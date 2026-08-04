'use client';

import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useCallback, useEffect, useState } from 'react';

import { EditorNotas } from '@/components/sesiones/EditorNotas';
import { PanelResultadoIA } from '@/components/sesiones/PanelResultadoIA';
import { Boton, Estado, Panel } from '@/components/ui';
import { api, ErrorAPI } from '@/lib/api';
import type { NotasEstructuradas } from '@/lib/types';
import estilos from './page.module.css';

export default function PaginaSesion() {
  return (
    <Suspense fallback={<Estado tipo="cargando" titulo="Abriendo sesión…" />}>
      <Contenido />
    </Suspense>
  );
}

function Contenido() {
  const { pacienteId } = useParams<{ pacienteId: string }>();
  const parametros = useSearchParams();
  const router = useRouter();

  const idInicial = parametros.get('sesion');
  const [sesionId, setSesionId] = useState<string | null>(idInicial);
  const [notas, setNotas] = useState('');
  // Sin `?sesion` no hay nada que traer: arranca lista sin pasar por el efecto.
  const [listo, setListo] = useState(!idInicial);

  const [resultado, setResultado] = useState<NotasEstructuradas | null>(null);
  const [procesando, setProcesando] = useState(false);
  const [errorIA, setErrorIA] = useState<string | null>(null);

  // Sesión existente: se trae el borrador. Sesión nueva: se arranca en blanco
  // y la fila se crea recién al guardar, para no dejar sesiones vacías.
  useEffect(() => {
    const id = parametros.get('sesion');
    if (!id) return;
    let vigente = true;
    (async () => {
      try {
        const sesion = await api.obtenerSesion(id);
        if (!vigente) return;
        setNotas(sesion.notas_borrador);
        setSesionId(sesion.id);
      } catch (e) {
        if (vigente) setErrorIA(e instanceof ErrorAPI ? e.message : 'Error inesperado.');
      } finally {
        if (vigente) setListo(true);
      }
    })();
    return () => {
      vigente = false;
    };
  }, [parametros]);

  /** Devuelve el id de la sesión, creándola si todavía no existe. */
  const asegurarSesion = useCallback(async (): Promise<string> => {
    if (sesionId) {
      await api.guardarBorrador(sesionId, notas);
      return sesionId;
    }
    const nueva = await api.crearSesion(pacienteId, notas);
    setSesionId(nueva.id);
    return nueva.id;
  }, [sesionId, notas, pacienteId]);

  const guardarBorrador = useCallback(
    (valor: string) => {
      if (!sesionId || !valor.trim()) return;
      api.guardarBorrador(sesionId, valor).catch(() => {
        /* el autoguardado no interrumpe: se reintenta en el próximo tecleo */
      });
    },
    [sesionId],
  );

  const procesar = useCallback(
    async (persistir: boolean) => {
      if (notas.trim().length < 10) {
        setErrorIA('Escribí al menos unas líneas antes de procesar.');
        return;
      }
      setProcesando(true);
      setErrorIA(null);
      try {
        const id = persistir ? await asegurarSesion() : undefined;
        const salida = await api.procesarNotas({
          notas,
          paciente_id: pacienteId,
          sesion_id: id,
          persistir,
        });
        setResultado(salida);
      } catch (e) {
        setErrorIA(e instanceof ErrorAPI ? e.message : 'Error inesperado.');
      } finally {
        setProcesando(false);
      }
    },
    [notas, pacienteId, asegurarSesion],
  );

  if (!listo) {
    return (
      <div className={estilos.centro}>
        <Estado tipo="cargando" titulo="Abriendo sesión…" />
      </div>
    );
  }

  return (
    <div className={estilos.pagina}>
      <div className={estilos.encabezado}>
        <div>
          <h1 className={estilos.titulo}>{sesionId ? 'Sesión' : 'Sesión nueva'}</h1>
          <p className={estilos.ayuda}>
            Escribí en borrador. La IA lo estructura sin tocar lo que anotaste.
          </p>
        </div>
        <div className={estilos.acciones}>
          <Boton variante="sutil" onClick={() => router.push(`/pacientes/${pacienteId}`)}>
            Volver
          </Boton>
          <Boton
            variante="secundario"
            onClick={() => procesar(false)}
            cargando={procesando}
            disabled={procesando}
          >
            Previsualizar
          </Boton>
          <Boton
            variante="primario"
            onClick={() => procesar(true)}
            cargando={procesando}
            disabled={procesando}
          >
            Procesar y guardar
          </Boton>
        </div>
      </div>

      <div className={estilos.grilla}>
        <Panel
          className={estilos.panelEditor}
          titulo="Notas de la sesión"
          meta={sesionId ? 'guardando automáticamente' : 'sin guardar todavía'}
          sinPadding
        >
          <EditorNotas
            valor={notas}
            onChange={setNotas}
            onGuardar={guardarBorrador}
            onProcesar={() => procesar(true)}
            deshabilitado={procesando}
          />
        </Panel>

        <Panel className={estilos.panelResultado} titulo="Lectura de la IA" sinPadding scroll>
          <PanelResultadoIA resultado={resultado} cargando={procesando} error={errorIA} />
        </Panel>
      </div>
    </div>
  );
}
