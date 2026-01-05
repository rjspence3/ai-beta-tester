import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Beta Tester',
  description: 'AI-powered exploratory testing dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <div className="flex flex-col min-h-screen">
          {/* Navigation */}
          <nav className="border-b border-gray-800 bg-gray-900/50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-between h-14">
                <div className="flex items-center space-x-8">
                  <Link href="/" className="text-lg font-semibold text-white">
                    AI Beta Tester
                  </Link>
                  <div className="flex space-x-4">
                    <Link
                      href="/sessions"
                      className="text-gray-400 hover:text-white transition-colors"
                    >
                      Sessions
                    </Link>
                    <Link
                      href="/sessions/new"
                      className="text-gray-400 hover:text-white transition-colors"
                    >
                      New Test
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </nav>

          {/* Main content */}
          <main className="flex-1">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
