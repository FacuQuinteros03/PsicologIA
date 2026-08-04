import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';

import { Encabezado } from '@/components/layout/Encabezado';
import './globals.css';
import estilos from './layout.module.css';

/** Geométrica y nítida, con tabular-nums disponible para las columnas. */
const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
  display: 'swap',
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'PsicoIA — Copiloto terapéutico',
  description: 'Gestión clínica con notas asistidas por IA y genograma interactivo.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es-AR" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        {/* Primer elemento focusable de la página: permite saltar la barra
            de navegación con Tab, sin usar el mouse. */}
        <a href="#contenido" className={estilos.saltar}>
          Saltar al contenido
        </a>
        <div className={estilos.marco}>
          <Encabezado />
          <main id="contenido" className={estilos.contenido}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
