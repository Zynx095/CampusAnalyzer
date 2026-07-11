"use client";

import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Command, Layout, Box, Image as ImageIcon, Sparkles, 
  ArrowRight, Trash2, Maximize2, Cpu, Upload, Leaf, Sun, 
  Car, Accessibility, Building, CheckCircle2 
} from "lucide-react";
import toast from "react-hot-toast";
import Navbar from "@/components/Navbar";
import SystemStatus from "@/components/SystemStatus";
import { useRouter } from "next/navigation";

const LOCAL_API_BASE = "http://127.0.0.1:8000";
const LOCAL_GENERATION_API = `${LOCAL_API_BASE}/api/local-generation`;
const CAMPUS_ANALYSIS_API = `${LOCAL_API_BASE}/api/campus/analyze`;

const LOCAL_SKILLS = [
  { name: "image-generation", label: "IMAGE", icon: <ImageIcon size={14} />, desc: "Open-ended visual synthesis." },
  { name: "poster-studio", label: "POSTER", icon: <Layout size={14} />, desc: "Campaign systems and typographic communication." },
  { name: "brand-concept", label: "BRAND", icon: <Box size={14} />, desc: "Identity directions and visual territories." },
  { name: "campus-vision", label: "CAMPUS", icon: <Leaf size={14} />, desc: "Future-facing architectural and spatial concepts." }
];

export default function PRANADashboard() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState({ status: "checking" });
  
  // Tabs: "studio", "analysis", "projects"
  const [activeTab, setActiveTab] = useState("studio");

  // Generation State
  const [input, setInput] = useState("");
  const [generating, setGenerating] = useState(false);
  const [generatedProjects, setGeneratedProjects] = useState([]);
  const [activeSkill, setActiveSkill] = useState(LOCAL_SKILLS[0]);
  const textareaRef = useRef(null);

  // Campus Analysis State
  const [analysisFile, setAnalysisFile] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    // Avoid synchronous setState during render by deferring mounting flag
    let isMounted = true;
    const mountTimer = setTimeout(() => {
      if (isMounted) setMounted(true);
    }, 0);

    const loadProjects = async () => {
      try {
        const { data } = await axios.get(`${LOCAL_API_BASE}/api/projects`);
        const projects = (data.projects || []).map((project) => ({
          ...project,
          assets: (project.assets || []).map((asset) => ({
            ...asset,
            url: asset.url.startsWith("http") ? asset.url : `${LOCAL_API_BASE}${asset.url}`
          }))
        }));
        if (isMounted) setGeneratedProjects(projects);
      } catch (err) {
        if (isMounted) console.error("Failed to load local projects:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    return () => {
      isMounted = false;
      clearTimeout(mountTimer);
    };

    const checkHealth = async () => {
      try {
        const { data } = await axios.get(`${LOCAL_GENERATION_API}/health`);
        if (isMounted) setHealth(data);
      } catch (err) {
        if (isMounted) setHealth({ status: "offline" });
      }
    };

    loadProjects();
    checkHealth();
    const healthInterval = setInterval(checkHealth, 30000);

    return () => {
      isMounted = false;
      clearInterval(healthInterval);
    };
  }, []);

  const generateLocally = async () => {
    const cleanPrompt = input.trim();
    if (!cleanPrompt || generating) return;

    setGenerating(true);
    const toastId = toast.loading("Initializing local inference engine...");

    try {
      const { data } = await axios.post(
        `${LOCAL_GENERATION_API}/image`,
        {
          prompt: cleanPrompt,
          mode: activeSkill.name,
          negative_prompt: "",
          width: activeSkill.name === "poster-studio" ? 512 : 768,
          height: activeSkill.name === "poster-studio" ? 768 : 768
        },
        { timeout: 1200000 }
      );

      const absoluteAssetUrl = data.asset_url.startsWith("http") ? data.asset_url : `${LOCAL_API_BASE}${data.asset_url}`;

      const localProject = {
        id: data.prompt_id,
        name: cleanPrompt,
        prompt: data.original_prompt,
        effective_prompt: data.effective_prompt,
        provider: data.provider,
        model: data.model,
        seed: data.seed,
        width: data.width,
        height: data.height,
        filename: data.filename,
        asset_url: data.asset_url,
        mode: data.mode,
        created_at: new Date().toISOString(),
        assets: [{ url: absoluteAssetUrl, kind: "image" }]
      };

      setGeneratedProjects((prev) => [localProject, ...prev]);
      setInput("");
      setActiveTab("projects");
      toast.success("Generation complete.", { id: toastId });
    } catch (err) {
      toast.error(`Inference Error: ${err?.response?.data?.detail || err?.message}`, { id: toastId });
    } finally {
      setGenerating(false);
    }
  };

  const handleAnalysisUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAnalysisFile(URL.createObjectURL(file));
    setAnalyzing(true);
    setAnalysisResult(null);

    const formData = new FormData();
    formData.append("image", file);

    const toastId = toast.loading("Running architectural vision analysis...");

    try {
      const { data } = await axios.post(CAMPUS_ANALYSIS_API, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setAnalysisResult(data);
      toast.success("Analysis complete.", { id: toastId });
    } catch (err) {
      toast.error(`Analysis Error: ${err?.response?.data?.detail || err?.message}`, { id: toastId });
      setAnalysisFile(null);
    } finally {
      setAnalyzing(false);
    }
  };

  const deleteProject = async (e, sessionId) => {
    e.stopPropagation();
    try {
      await axios.delete(`${LOCAL_API_BASE}/api/projects/${encodeURIComponent(sessionId)}`);
      setGeneratedProjects((prev) => prev.filter((p) => p.id !== sessionId));
      toast.success("Project purged.");
    } catch (err) {
      toast.error("Could not purge project.");
    }
  };

  if (!mounted) return null;

  return (
    <div className="min-h-dvh w-full bg-background selection:bg-accent selection:text-black">
      <Navbar />
      
      <main className="pt-24 pb-20 px-6 lg:px-12 max-w-[1800px] mx-auto flex flex-col gap-12">
        
        {/* Header & Telemetry */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mt-8">
          <div className="flex flex-col gap-2">
            <h1 className="text-4xl md:text-5xl font-light tracking-tight text-primary">
              Design <span className="text-secondary">Intelligence.</span>
            </h1>
            <p className="text-sm font-mono text-muted uppercase tracking-widest">
              Local Inference Engine · Operational
            </p>
          </div>
          <SystemStatus health={health} />
        </div>

        {/* Custom Segmented Control */}
        <div className="flex items-center gap-2 border-b border-architectural pb-px">
          {["studio", "analysis", "projects"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`relative px-6 py-3 text-xs font-mono tracking-widest uppercase transition-colors ${activeTab === tab ? 'text-accent' : 'text-secondary hover:text-primary'}`}
            >
              {tab === "studio" ? "Creation Studio" : tab === "analysis" ? "Campus Analysis" : "Project Library"}
              {activeTab === tab && (
                <motion.div layoutId="activeTab" className="absolute bottom-0 inset-x-0 h-px bg-accent" />
              )}
            </button>
          ))}
        </div>

        {/* Tab Content Area */}
        <AnimatePresence mode="wait">
          
          {/* TAB 1: STUDIO */}
          {activeTab === "studio" && (
            <motion.section 
              key="studio"
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
              className="w-full max-w-5xl flex flex-col gap-6"
            >
              <div className="glass-panel p-2 rounded-md focus-within:border-accent/50 transition-colors">
                <textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); generateLocally(); } }}
                  placeholder="Describe the architectural concept, visual system, or typographic poster..."
                  className="w-full bg-transparent border-none focus:ring-0 text-lg md:text-xl p-6 h-48 resize-none placeholder:text-muted outline-none font-light leading-relaxed"
                  disabled={generating}
                />
                
                <div className="flex flex-col sm:flex-row items-center justify-between p-4 border-t border-architectural gap-4">
                  <div className="flex flex-wrap gap-2">
                    {LOCAL_SKILLS.map(skill => (
                      <button
                        key={skill.name}
                        onClick={() => setActiveSkill(skill)}
                        className={`flex items-center gap-2 px-4 py-2 text-[10px] font-mono tracking-widest uppercase rounded-sm border transition-all ${
                          activeSkill.name === skill.name 
                            ? "bg-accent/10 border-accent/40 text-accent shadow-[0_0_15px_rgba(163,255,18,0.1)]" 
                            : "bg-elevated border-architectural text-secondary hover:border-muted hover:text-primary"
                        }`}
                      >
                        {skill.icon} {skill.label}
                      </button>
                    ))}
                  </div>

                  <button 
                    onClick={generateLocally}
                    disabled={!input.trim() || generating}
                    className={`flex items-center gap-3 px-8 py-3 text-xs font-mono tracking-widest uppercase rounded-sm transition-all ${
                      input.trim() && !generating
                        ? "bg-primary text-background hover:bg-accent hover:text-black"
                        : "bg-elevated text-muted border border-architectural cursor-not-allowed"
                    }`}
                  >
                    {generating ? <><Sparkles size={14} className="animate-spin" /> INFERRING</> : <><Command size={14} /> GENERATE</>}
                  </button>
                </div>
              </div>
              <div className="text-[10px] font-mono text-muted tracking-widest uppercase px-2">
                ACTIVE PIPELINE: {activeSkill.name === "poster-studio" ? "QWEN GGUF (512x768)" : "FLUX SCHNELL (768x768)"}
              </div>
            </motion.section>
          )}

          {/* TAB 2: CAMPUS ANALYSIS */}
          {activeTab === "analysis" && (
            <motion.section 
              key="analysis"
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
              className="w-full grid grid-cols-1 lg:grid-cols-2 gap-8"
            >
              <div className="flex flex-col gap-6">
                <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={handleAnalysisUpload} />
                
                {!analysisFile ? (
                  <button 
                    onClick={() => fileInputRef.current?.click()}
                    className="w-full aspect-[4/3] glass-panel border-dashed border-muted hover:border-accent flex flex-col items-center justify-center gap-4 transition-colors group rounded-sm"
                  >
                    <div className="p-4 rounded-full bg-elevated group-hover:bg-accent/10 transition-colors">
                      <Upload size={24} className="text-secondary group-hover:text-accent" />
                    </div>
                    <div className="flex flex-col items-center gap-1 text-center">
                      <span className="text-sm font-mono uppercase tracking-widest text-primary">Upload Campus Imagery</span>
                      <span className="text-xs text-muted">JPEG, PNG up to 15MB</span>
                    </div>
                  </button>
                ) : (
                  <div className="w-full aspect-[4/3] glass-panel rounded-sm overflow-hidden relative group">
                    <img src={analysisFile} alt="Analysis" className="w-full h-full object-cover" />
                    <button onClick={() => { setAnalysisFile(null); setAnalysisResult(null); }} className="absolute top-4 right-4 p-2 bg-background/80 backdrop-blur rounded-sm text-secondary hover:text-red-400 border border-architectural">
                      <Trash2 size={14} />
                    </button>
                  </div>
                )}
              </div>

              <div className="glass-panel rounded-sm p-8 flex flex-col">
                {analyzing ? (
                  <div className="h-full flex flex-col items-center justify-center gap-6">
                    <div className="relative w-16 h-16">
                      <div className="absolute inset-0 border border-accent/20 rounded-full animate-ping" />
                      <div className="absolute inset-2 border border-accent/40 rounded-full animate-spin" />
                      <Sparkles size={20} className="absolute inset-0 m-auto text-accent" />
                    </div>
                    <span className="text-xs font-mono tracking-widest text-accent uppercase animate-pulse">Running Vision Diagnostics</span>
                  </div>
                ) : analysisResult ? (
                  <div className="flex flex-col gap-8 h-full overflow-y-auto custom-scrollbar pr-2">
                    <div className="flex items-end justify-between border-b border-architectural pb-6">
                      <div className="flex flex-col gap-1">
                        <span className="text-[10px] font-mono tracking-widest text-accent uppercase">Overall Rating</span>
                        <span className="text-4xl font-light text-primary">{analysisResult.overall_score}<span className="text-muted text-lg">/100</span></span>
                      </div>
                      <div className="px-3 py-1 bg-elevated border border-architectural rounded-sm text-xs font-mono uppercase text-secondary">
                        Condition: <span className="text-primary">{analysisResult.building_condition}</span>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      {[
                        { label: "Green Cover", val: analysisResult.green_cover, icon: <Leaf size={14}/> },
                        { label: "Walkability", val: analysisResult.walkability, icon: <Accessibility size={14}/> },
                        { label: "Solar Potential", val: analysisResult.solar_potential, icon: <Sun size={14}/> },
                        { label: "Parking Efficiency", val: analysisResult.parking_efficiency, icon: <Car size={14}/> }
                      ].map(metric => (
                        <div key={metric.label} className="flex flex-col p-4 bg-elevated border border-architectural rounded-sm gap-3">
                          <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-widest text-muted">
                            {metric.icon} {metric.label}
                          </div>
                          <div className="w-full h-1 bg-background rounded-full overflow-hidden">
                            <motion.div initial={{ width: 0 }} animate={{ width: `${metric.val}%` }} className="h-full bg-accent" transition={{ duration: 1, ease: "easeOut" }} />
                          </div>
                          <div className="text-lg font-light text-primary">{metric.val}%</div>
                        </div>
                      ))}
                    </div>

                    <div className="flex flex-col gap-2">
                      <span className="text-[10px] font-mono tracking-widest text-secondary uppercase">Architectural Summary</span>
                      <p className="text-sm text-primary leading-relaxed">{analysisResult.summary}</p>
                    </div>

                    <div className="flex flex-col gap-3">
                      <span className="text-[10px] font-mono tracking-widest text-secondary uppercase">Strategic Upgrades</span>
                      {analysisResult.recommendations.map((rec, i) => (
                        <div key={i} className="flex items-start gap-3 p-3 bg-accent/5 border border-accent/20 rounded-sm">
                          <CheckCircle2 size={14} className="text-accent mt-0.5 shrink-0" />
                          <p className="text-xs text-primary leading-relaxed">{rec}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-muted gap-4">
                    <Building size={32} className="opacity-50" />
                    <span className="text-xs font-mono tracking-widest uppercase text-center leading-relaxed">
                      Awaiting spatial input.<br/>Upload imagery to commence diagnostics.
                    </span>
                  </div>
                )}
              </div>
            </motion.section>
          )}

          {/* TAB 3: PROJECTS */}
          {activeTab === "projects" && (
            <motion.section 
              key="projects"
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
              className="w-full"
            >
              {generatedProjects.length === 0 ? (
                <div className="w-full py-32 flex flex-col items-center justify-center glass-panel rounded-sm gap-4">
                  <Box size={32} className="text-muted opacity-50" />
                  <span className="text-xs font-mono tracking-widest text-secondary uppercase">No Systems Generated</span>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {generatedProjects.map((session) => (
                    <div 
                      key={session.id}
                      onClick={() => router.push(`/canvas?session=${session.id}`)}
                      className="group relative aspect-[4/5] glass-panel rounded-sm overflow-hidden cursor-pointer hover:border-accent/50 transition-colors"
                    >
                      {session.assets?.[0]?.url ? (
                        <img src={session.assets[0].url} alt={session.name} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-all duration-700 group-hover:scale-105" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-elevated"><ImageIcon size={32} className="text-muted" /></div>
                      )}
                      
                      <button onClick={(e) => deleteProject(e, session.id)} className="absolute top-4 right-4 p-2 bg-background/80 backdrop-blur rounded-sm text-secondary hover:text-red-400 border border-architectural opacity-0 group-hover:opacity-100 transition-all">
                        <Trash2 size={14} />
                      </button>

                      <div className="absolute inset-x-0 bottom-0 p-5 bg-gradient-to-t from-background via-background/90 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end">
                        <span className="w-max px-2 py-1 bg-accent/20 border border-accent/30 text-[9px] font-mono tracking-widest text-accent uppercase rounded-sm mb-3">
                          {session.mode?.replace(/-/g, ' ')}
                        </span>
                        <h4 className="text-sm font-medium text-primary line-clamp-2 leading-snug">{session.prompt}</h4>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.section>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}