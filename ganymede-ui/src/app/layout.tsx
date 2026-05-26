import type { Metadata } from 'next';
import { Inter, Space_Grotesk, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { AuthPill } from '@/components/AuthPill';

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
        <AuthPill />
        {children}
      </body>
    </html>
  );
}
