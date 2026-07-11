import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Toaster } from "react-hot-toast";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "PRANA | Design Intelligence",
  description: "Local-first AI creative intelligence and architectural system",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} antialiased`}>
        <Providers>
          {children}
        </Providers>
        <Toaster 
          position="top-right" 
          toastOptions={{
            style: {
              background: '#0A0A0A',
              color: '#FAFAFA',
              border: '1px solid rgba(255,255,255,0.06)',
              fontSize: '12px',
              fontFamily: 'monospace',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }
          }}
        />
      </body>
    </html>
  );
}