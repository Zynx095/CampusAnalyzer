"use client";

import React from "react";
import { Cpu, HardDrive } from "lucide-react";
import { motion } from "framer-motion";

export default function SystemStatus({ health }) {
  const isOnline = health?.status === "online";

  return (
    <div className="flex items-center gap-4 text-[10px] font-mono tracking-widest uppercase">
      <div className="flex items-center gap-2 px-3 py-1.5 glass-panel rounded-sm shadow-2xl">
        <Cpu size={12} className={isOnline ? "text-primary" : "text-muted"} />
        <span className="text-secondary hidden sm:inline">GPU</span>
        <span className="text-primary">RTX 5050</span>
      </div>
      
      <div className="flex items-center gap-2 px-3 py-1.5 glass-panel rounded-sm shadow-2xl">
        <HardDrive size={12} className={isOnline ? "text-primary" : "text-muted"} />
        <span className="text-secondary hidden sm:inline">VRAM</span>
        <span className="text-primary">8 GB</span>
      </div>

      <div className="flex items-center gap-2 px-3 py-1.5 glass-panel rounded-sm shadow-2xl">
        <motion.div 
          animate={isOnline ? { opacity: [1, 0.4, 1] } : {}} 
          transition={{ duration: 2, repeat: Infinity }}
        />
      </div>
    </div>
  );
}