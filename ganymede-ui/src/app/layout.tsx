import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Project Ganymede | 9D Strategic Engine',
  description: 'Simulation sandbox for running real scenarios through the 9D strategic-physics framework.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // suppressHydrationWarning silences the Next.js dev-overlay "1 Issue"
    // chip caused by browser extensions (Darkreader, etc.) injecting
    // attributes into <html> after SSR but before React hydrates. The
    // attributes (`data-darkreader-mode`, `data-darkreader-proxy-injected`)
    // are client-only and there's nothing we can do server-side to match
    // them. React 18+ allows this single attribute to skip hydration mismatch
    // warnings for known-divergent root attributes; it does NOT suppress
    // other hydration mismatches that we DO want to know about.
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="antialiased bg-[#030712] text-slate-200">
        {children}
      </body>
    </html>
  );
}
