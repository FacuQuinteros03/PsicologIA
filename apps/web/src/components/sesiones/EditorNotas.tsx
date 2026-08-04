'use client';

import { useEffect, useRef, useState } from 'react';
import type { KeyboardEvent } from 'react';

import estilos from './EditorNotas.module.css';

export interface PropsEditorNotas {
  valor: string;
  onChange: (valor: string) => void;
  /** Se llama tras 1,2 s sin tipear. Autoguardado del borrador. */
  onGuardar?: (valor: string) => void;
  /** Atajo Ctrl/Cmd + Enter. */
  onProcesar?: () => void;
  deshabilitado?: boolean;
}

/**
 * Área de escritura de la sesión.
 *
 * Pensada para usarse mientras se atiende: sin barra de formato, sin
 * distracciones, y con el foco puesto al montar. `Ctrl + Enter` procesa sin
 * tener que ir al botón.
 */
export function EditorNotas({
  valor,
  onChange,
  onGuardar,
  onProcesar,
  deshabilitado = false,
}: PropsEditorNotas) {
  const areaRef = useRef<HTMLTextAreaElement>(null);
  const [guardado, setGuardado] = useState<'limpio' | 'pendiente' | 'guardando'>('limpio');

  useEffect(() => {
    areaRef.current?.focus();
  }, []);

  // Autoguardado con debounce. El temporizador se reinicia en cada tecla.
  useEffect(() => {
    if (!onGuardar || guardado !== 'pendiente') return;
    const temporizador = setTimeout(() => {
      setGuardado('guardando');
      onGuardar(valor);
      setGuardado('limpio');
    }, 1200);
    return () => clearTimeout(temporizador);
  }, [valor, guardado, onGuardar]);

  function alPresionar(evento: KeyboardEvent<HTMLTextAreaElement>) {
    if ((evento.ctrlKey || evento.metaKey) && evento.key === 'Enter') {
      evento.preventDefault();
      onProcesar?.();
    }
  }

  const palabras = valor.trim() ? valor.trim().split(/\s+/).length : 0;

  return (
    <div className={estilos.contenedor}>
      <textarea
        ref={areaRef}
        className={estilos.area}
        value={valor}
        disabled={deshabilitado}
        spellCheck
        placeholder={
          '- llegó angustiada, semana dura en el trabajo\n' +
          '- discusión con la mamá el domingo\n' +
          '- duerme mal hace 3 semanas'
        }
        aria-label="Notas de la sesión"
        onChange={(e) => {
          onChange(e.target.value);
          setGuardado('pendiente');
        }}
        onKeyDown={alPresionar}
      />

      <div className={estilos.pie}>
        <span className={`${estilos.contador} tabular`}>
          {palabras} {palabras === 1 ? 'palabra' : 'palabras'}
        </span>
        <span className={estilos.guardado}>
          {guardado === 'limpio' ? 'Guardado' : 'Guardando…'}
        </span>
        <span className={estilos.atajo}>
          <kbd>Ctrl</kbd> + <kbd>Enter</kbd> para procesar
        </span>
      </div>
    </div>
  );
}
