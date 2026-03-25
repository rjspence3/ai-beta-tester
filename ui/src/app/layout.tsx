import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'AI Beta Tester — Personality-driven web testing',
  description: 'AI agents with distinct personalities browse your app to surface bugs you can\'t see. 13 testers, Claude-powered, Playwright automation.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.className}>
      <body className="min-h-screen bg-[#F8F9FC] text-[#111827]">
        {children}
      </body>
    </html>
  );
}
