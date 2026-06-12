import type { Metadata } from 'next';
import { Inter, Space_Grotesk, JetBrains_Mono } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const spaceGrotesk = Space_Grotesk({ subsets: ['latin'], variable: '--font-space' });
const jetBrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono' });

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
    <html lang="en" className="dark">
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
