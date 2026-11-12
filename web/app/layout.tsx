import type { Metadata } from "next";
import type { ReactNode } from "react";
import localFont from "next/font/local";
import "./globals.css";

const fonte = localFont({
  src: "../fonts/dm-sans/DMSans-latin.woff2",
  weight: "400 700",
  style: "normal",
});

export const metadata: Metadata = {
  title: "LogiDash — Painel de entregas",
  description: "OTIF do período e linhas que não entram na métrica",
};

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className={fonte.className}>{children}</body>
    </html>
  );
}
