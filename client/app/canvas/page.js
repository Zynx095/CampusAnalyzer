"use client";

import React, { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Image from "next/image";
import axios from "axios";
import { motion } from "framer-motion";
import { 
  ArrowLeft, Image as ImageIcon, Trash2, Maximize2, 
  Clock, Cpu, Hash, Layout, Info, Sparkles, Download
} from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

const LOCAL_API_BASE = "http://127.0.0.1:8000";

function ProjectDetail() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const projectId = searchParams.get("session");

  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const fetchProject = async () => {
      if (!projectId) {
        if (isMounted) { setError("No project ID specified."); setLoading(false); }
        return;
      }
      try {
        const { data } = await axios.get(`${LOCAL_API_BASE}/api/projects/${encodeURIComponent(projectId)}`);
        const projData = data.project || data;
        if (isMounted) { setProject(projData); setLoading(false); }
      } catch (err) {
        if (isMounted) {
          setError(err?.response?.data?.detail || "Failed to load project metadata.");
          setLoading(false);
        }
      }
    };
    fetchProject();
    return () => { isMounted = false; };
  }, [projectId]);

  const handleDelete = async () => {
    if (!project) return;
    try {
      await axios.delete(`${LOCAL_API_BASE}/api/projects/${encodeURIComponent(project.id)}`);
      toast.success("Project purged.");
      router.push("/");
    } catch (err) {
      toast.error("Failed to delete project.");
    }
  };

  if (loading) return (
    <div className="h-dvh w-full flex flex-col items-center justify-center bg-background text-primary gap-6">
      <Sparkles size={24} className="animate-spin text-accent" />
      <div className="text-[10px] font-mono tracking-widest text-muted uppercase">Extracting Archive</div>
    </div>
  );

  if (error || !project) return (
    <div className="h-dvh w-full flex flex-col items-center justify-center bg-background text-primary gap-6">
      <Info size={32} className="text-red-500" />
      <div className="text-xs font-mono tracking-widest text-red-500 uppercase">Archive Fracture</div>
      <Link href="/" className="px-6 py-2 border border-architectural text-[10px] font-mono uppercase tracking-widest hover:text-accent rounded-sm">Return to Studio</Link>
    </div>
  );

  const mainAsset = project.assets?.[0];
  const assetUrl = mainAsset?.url?.startsWith("http") ? mainAsset.url : mainAsset?.url ? `${LOCAL_API_BASE}${mainAsset.url}` : null;
  const creationDate = project.created_at ? new Date(project.created_at).toLocaleString() : "Unknown";

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-dvh w-full flex flex-col lg:flex-row bg-background text-primary">
      
      {/* Visual Canvas */}
      <div className="w-full lg:w-2/3 h-[50vh] lg:h-full bg-[#050505] border-r border-architectural relative p-8 flex items-center justify-center">
        <Link href="/" className="absolute top-6 left-6 z-10 flex items-center gap-2 px-4 py-2 bg-background/80 backdrop-blur border border-architectural text-[10px] font-mono tracking-widest uppercase hover:text-accent transition-colors rounded-sm">
          <ArrowLeft size={12} /> Studio
        </Link>

        {assetUrl ? (
          <div className="relative w-full h-full">
            <Image src={assetUrl} alt={project.prompt} fill unoptimized className="object-contain drop-shadow-2xl" />
          </div>
        ) : (
          <div className="flex flex-col items-center text-muted gap-4"><ImageIcon size={32} /><span className="text-xs font-mono uppercase">Asset Unavailable</span></div>
        )}
      </div>

      {/* Intelligence Panel */}
      <div className="w-full lg:w-1/3 h-[50vh] lg:h-full overflow-y-auto custom-scrollbar bg-surface/50 backdrop-blur-xl">
        <div className="p-8 lg:p-12 flex flex-col gap-10">
          
          <div className="flex flex-col gap-3">
            <span className="text-[10px] font-mono tracking-widest text-accent uppercase">Original Intent</span>
            <p className="text-base text-primary leading-relaxed font-light">{project.prompt}</p>
          </div>

          <div className="flex flex-col gap-3">
            <span className="text-[10px] font-mono tracking-widest text-secondary uppercase">Deterministic Prompt</span>
            <div className="p-4 bg-background border border-architectural rounded-sm">
              <p className="text-xs text-secondary leading-relaxed font-mono">{project.effective_prompt}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-6 pt-6 border-t border-architectural">
            {[
              { label: "Model", val: project.model, icon: Cpu },
              { label: "Dimensions", val: `${project.width} × ${project.height}`, icon: Layout },
              { label: "Seed", val: project.seed, icon: Hash },
              { label: "Mode", val: project.mode?.replace(/-/g, ' '), icon: Sparkles },
            ].map((stat, i) => (
              <div key={i} className="flex flex-col gap-2">
                <span className="text-[9px] font-mono text-muted uppercase tracking-widest flex items-center gap-2">
                  <stat.icon size={10}/> {stat.label}
                </span>
                <span className="text-xs font-mono text-primary truncate uppercase">{stat.val}</span>
              </div>
            ))}
            <div className="flex flex-col gap-2 col-span-2">
              <span className="text-[9px] font-mono text-muted uppercase tracking-widest flex items-center gap-2">
                <Clock size={10}/> Inference Time
              </span>
              <span className="text-xs font-mono text-primary">{creationDate}</span>
            </div>
          </div>

          <div className="flex flex-col gap-3 pt-6 border-t border-architectural mt-auto">
            {assetUrl && (
              <a href={assetUrl} download target="_blank" rel="noopener noreferrer" className="flex items-center justify-between px-4 py-3 bg-primary text-background hover:bg-accent transition-colors rounded-sm text-[10px] font-mono tracking-widest uppercase">
                <span className="flex items-center gap-2"><Download size={14}/> Download HD</span>
              </a>
            )}
            <button onClick={handleDelete} className="flex items-center justify-between px-4 py-3 bg-transparent border border-red-900/30 text-red-500 hover:bg-red-500/10 transition-colors rounded-sm text-[10px] font-mono tracking-widest uppercase mt-4">
              <span className="flex items-center gap-2"><Trash2 size={14}/> Purge Record</span>
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function CanvasPage() {
  return (
    <Suspense fallback={<div className="h-dvh w-full bg-background" />}>
      <ProjectDetail />
    </Suspense>
  );
}