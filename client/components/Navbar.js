"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Hexagon } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="fixed top-0 inset-x-0 z-50 h-16 glass-panel border-t-0 border-x-0 transition-colors duration-300">
      <div className="flex h-full items-center justify-between px-6 lg:px-12 max-w-[1800px] mx-auto">
        <div className="flex items-center gap-12">
          <Link href="/" className="flex items-center gap-3 text-primary hover:text-accent transition-colors">
            <Hexagon size={18} className="text-accent" />
            <span className="font-bold tracking-[0.2em] text-xs uppercase mt-0.5">PRANA</span>
          </Link>
          
          <nav className="hidden md:flex items-center gap-8 text-[10px] font-mono text-secondary uppercase tracking-widest">
            <Link href="/" className={`transition-colors ${pathname === '/' ? 'text-accent' : 'hover:text-primary'}`}>
              Studio Workspace
            </Link>
            <span className="cursor-not-allowed opacity-50">Intelligence Node</span>
            <span className="cursor-not-allowed opacity-50">Settings</span>
          </nav>
        </div>
      </div>
    </header>
  );
}