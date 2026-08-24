import type { Metadata } from 'next';
import { Inter, Space_Grotesk, JetBrains_Mono } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const spaceGrotesk = Space_Grotesk({ subsets: ['latin'], variable: '--font-space' });
const jetBrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' });

export const metadata: Metadata = {
  title: 'Project Ganymede | 9D Strategic Engine',
  description:
    'The real Project Ganymede interface: a deterministic showroom for its strategic-physics engine, audit loop, and lithography visualization.',
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
      <body className={`${inter.variable} ${spaceGrotesk.variable} ${jetBrainsMono.variable} antialiased bg-[#030712] text-slate-200`}>
        {/* AuthPill is no longer mounted globally — it lives inside the
            SettingsTray on the main page (see app/page.tsx). Sub-pages
            without a SettingsTray (currently just /predictions) reach the
            relogin flow from the main page; they're read-only views. */}
        {children}
      </body>
    </html>
  );
}
