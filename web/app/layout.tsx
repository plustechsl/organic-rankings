import type { Metadata } from 'next';
import './globals.css';
import Navbar from '@/app/components/Navbar';
import Footer from '@/app/components/Footer';

export const metadata: Metadata = {
  title: 'Organic Rankings',
  description: 'Donde el ranking lo decide la gente, no un algoritmo opaco.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang=\"es\">
      <body className=\"flex min-h-screen flex-col bg-white text-gray-900\">
        <Navbar />
        <main className=\"mx-auto w-full max-w-6xl flex-1 px-4 py-8\">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
