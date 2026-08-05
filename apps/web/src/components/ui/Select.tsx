"use client";

import { useId, useState, useRef, useEffect } from "react";
import type { SelectHTMLAttributes } from "react";
import estilos from "./Select.module.css";

export interface OpcionSelect<T extends string = string> {
  valor: T;
  etiqueta: string;
}

export interface PropsSelect<T extends string = string> extends Omit<
  SelectHTMLAttributes<HTMLSelectElement>,
  "className" | "children" | "onChange"
> {
  etiqueta?: string;
  opciones: readonly OpcionSelect<T>[];
  ayuda?: string;
  error?: string;
  placeholder?: string;
  className?: string;
  value?: T | "";
  onChange?: (e: { target: { value: T | "" } }) => void;
}

export function Select<T extends string = string>({
  etiqueta,
  opciones,
  ayuda,
  error,
  placeholder,
  className,
  value = "",
  onChange,
  disabled,
}: PropsSelect<T>) {
  const id = useId();
  const [abierto, setAbierto] = useState(false);
  const contenedorRef = useRef<HTMLDivElement>(null);

  const opcionSeleccionada = opciones.find((o) => o.valor === value);

  // Cerrar al hacer click afuera
  useEffect(() => {
    function clickAfuera(e: MouseEvent) {
      if (
        contenedorRef.current &&
        !contenedorRef.current.contains(e.target as Node)
      ) {
        setAbierto(false);
      }
    }
    document.addEventListener("mousedown", clickAfuera);
    return () => document.removeEventListener("mousedown", clickAfuera);
  }, []);

  function seleccionar(val: T | "") {
    onChange?.({ target: { value: val } });
    setAbierto(false);
  }

  return (
    <div
      className={[estilos.grupo, className ?? ""].filter(Boolean).join(" ")}
      ref={contenedorRef}
    >
      {etiqueta && (
        <label className={estilos.etiqueta} htmlFor={id}>
          {etiqueta}
        </label>
      )}

      <div className={estilos.envoltorio}>
        <button
          type="button"
          id={id}
          disabled={disabled}
          className={`${estilos.control} ${error ? estilos.conError : ""} ${abierto ? estilos.abierto : ""}`}
          onClick={() => setAbierto(!abierto)}
          aria-haspopup="listbox"
          aria-expanded={abierto}
        >
          <span
            className={
              opcionSeleccionada ? estilos.textoValor : estilos.placeholder
            }
          >
            {opcionSeleccionada
              ? opcionSeleccionada.etiqueta
              : placeholder || "Seleccionar…"}
          </span>
          <span
            className={`${estilos.flecha} ${abierto ? estilos.flechaGirada : ""}`}
          />
        </button>

        {abierto && (
          <ul className={estilos.menu} role="listbox">
            {placeholder && (
              <li
                className={`${estilos.opcion} ${value === "" ? estilos.opcionSeleccionada : ""}`}
                onClick={() => seleccionar("")}
                role="option"
                aria-selected={value === ""}
              >
                {placeholder}
              </li>
            )}
            {opciones.map((op) => (
              <li
                key={op.valor}
                className={`${estilos.opcion} ${value === op.valor ? estilos.opcionSeleccionada : ""}`}
                onClick={() => seleccionar(op.valor)}
                role="option"
                aria-selected={value === op.valor}
              >
                {op.etiqueta}
              </li>
            ))}
          </ul>
        )}
      </div>

      {(ayuda || error) && (
        <p
          className={error ? estilos.error : estilos.ayuda}
          role={error ? "alert" : undefined}
        >
          {error ?? ayuda}
        </p>
      )}
    </div>
  );
}
