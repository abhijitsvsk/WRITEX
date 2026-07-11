"use client";
import React, { useState } from "react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"text" | "upload" | "academic">("text");
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [images, setImages] = useState<FileList | null>(null);
  const [imagePlacement, setImagePlacement] = useState("Let AI Decide");
  
  const [margin, setMargin] = useState(1.0);
  const [hFont, setHFont] = useState("Times New Roman");
  const [hSize, setHSize] = useState(14);
  const [chapAlign, setChapAlign] = useState("Center");
  const [subhAlign, setSubhAlign] = useState("Left");
  const [hBold, setHBold] = useState(true);
  
  const [cFont, setCFont] = useState("Times New Roman");
  const [cSize, setCSize] = useState(12);
  const [cAlign, setCAlign] = useState("Justify");
  const [codeLang, setCodeLang] = useState("Auto");
  
  const [spacing, setSpacing] = useState(1.5);
  const [spaceBefore, setSpaceBefore] = useState(0);
  const [spaceAfter, setSpaceAfter] = useState(0);
  const [continuous, setContinuous] = useState(false);

  const [projZip, setProjZip] = useState<File | null>(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [sampleRep, setSampleRep] = useState<File | null>(null);
  const [rewriteMode, setRewriteMode] = useState(false);
  const [testMetrics, setTestMetrics] = useState<File | null>(null);
  const [projTitle, setProjTitle] = useState("");
  const [degree, setDegree] = useState("");
  const [university, setUniversity] = useState("");
  const [department, setDepartment] = useState("");
  const [academicYear, setAcademicYear] = useState("");
  const [principal, setPrincipal] = useState("");
  const [hod, setHod] = useState("");
  const [guide, setGuide] = useState("");
  const [guideDesignation, setGuideDesignation] = useState("");
  const [hodDesignation, setHodDesignation] = useState("");
  const [teamMembersString, setTeamMembersString] = useState("");
  const [specialRequestText, setSpecialRequestText] = useState("");
  
  const [conflicts, setConflicts] = useState<any[]>([]);
  const [showConflictModal, setShowConflictModal] = useState(false);
  const [resolvedConflicts, setResolvedConflicts] = useState<Record<string, any>>({});

  const handleGenerate = async (isRetryWithResolutions = false) => {
    if (!apiKey) { setError("Please provide an API Key."); return; }
    setError("");
    setLoading(true);
    
    const formData = new FormData();
    formData.append("api_key", apiKey);
    
    let endpoint = "";

    if (activeTab === "text" || activeTab === "upload") {
      endpoint = activeTab === "text" ? "http://localhost:8000/api/format_text" : "http://localhost:8000/api/format_file";
      formData.append("image_placement", imagePlacement);
      formData.append("style_name", "Academic");
      
      const styleConfig = { margin_inches: margin, heading_font: hFont, heading_size_pt: hSize, heading_bold: hBold, chapter_alignment: chapAlign, subheading_alignment: subhAlign, content_font: cFont, content_size_pt: cSize, content_alignment: cAlign, line_spacing: spacing, space_before_pt: spaceBefore, space_after_pt: spaceAfter, code_language: codeLang, continuous_sections: continuous };
      formData.append("style_config", JSON.stringify(styleConfig));
      
      if (images) { for (let i = 0; i < images.length; i++) formData.append("images", images[i]); }
      if (activeTab === "text") {
        if (!text) { setError("Please provide some raw text."); setLoading(false); return; }
        formData.append("text", text);
      } else {
        if (!file) { setError("Please upload a document."); setLoading(false); return; }
        formData.append("file", file);
      }
    } else if (activeTab === "academic") {
      endpoint = "http://localhost:8000/api/format_academic_report";
      if (!projZip && !githubUrl) { setError("Please provide a Project ZIP or GitHub URL."); setLoading(false); return; }
      if (projZip) formData.append("proj_zip", projZip);
      formData.append("github_url", githubUrl);
      if (sampleRep) formData.append("sample_rep", sampleRep);
      formData.append("rewrite_mode", rewriteMode ? "true" : "false");
      if (testMetrics) formData.append("test_metrics", testMetrics);
      formData.append("title", projTitle);
      formData.append("degree", degree);
      formData.append("university", university);
      formData.append("department", department);
      formData.append("academic_year", academicYear);
      formData.append("principal", principal);
      formData.append("hod", hod);
      formData.append("guide", guide);
      formData.append("guide_designation", guideDesignation);
      formData.append("hod_designation", hodDesignation);
      const teamArr = teamMembersString.split(",").map(n => n.trim()).filter(Boolean);
      formData.append("team_names", teamArr.join(","));
      formData.append("special_request_text", specialRequestText);
      formData.append("resolved_conflicts", JSON.stringify(resolvedConflicts));
    }
    
    try {
      const response = await fetch(endpoint, { method: "POST", body: formData });
      if (response.status === 409) {
        const data = await response.json();
        setConflicts(data.conflicts);
        setShowConflictModal(true);
        setLoading(false);
        return;
      }
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Generation failed.");
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = activeTab === "academic" ? "Academic_Report.docx" : "formatted.docx";
      a.click();
      window.URL.revokeObjectURL(url);
      if (isRetryWithResolutions) { setShowConflictModal(false); setConflicts([]); setResolvedConflicts({}); }
    } catch (err: any) { setError(err.message); } finally { setLoading(false); }
  };

  const resolveConflict = (key: string, value: any) => { setResolvedConflicts(prev => ({ ...prev, [key]: value })); };

  return (
    <div className="min-h-screen text-on-surface bg-background relative overflow-hidden">
        {/* Atmospheric Background Components */}
        <div className="blob bg-primary top-[-10%] left-[-10%]"></div>
        <div class="blob bg-tertiary bottom-[-10%] right-[-10%] opacity-20"></div>
        <div class="blob bg-secondary top-[40%] right-[10%] opacity-20"></div>

        {/* Navigation Shell */}
        <nav className="fixed top-0 w-full z-50 bg-surface/30 backdrop-blur-xl border-b border-white/10 shadow-[0_0_20px_rgba(79,70,229,0.15)]">
            <div className="flex justify-between items-center px-8 md:px-16 py-4 max-w-7xl mx-auto">
                <div className="flex items-center gap-4">
                    <span className="text-2xl font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">WriteX</span>
                </div>
                <div className="hidden md:flex gap-8 items-center">
                   <input type="password" value={apiKey} onChange={e=>setApiKey(e.target.value)} placeholder="API Key (Groq/DeepSeek)" className="bg-white/5 border border-white/10 rounded-lg px-4 py-1.5 text-sm outline-none focus:border-primary w-64" />
                </div>
            </div>
        </nav>

        {/* Main Content Area */}
        <main className="pt-32 pb-16 px-4 md:px-0">
            <div className="max-w-4xl mx-auto">
                
                {error && <div className="mb-4 p-4 rounded-lg bg-error-container text-on-error-container text-sm text-center border border-error/50 shadow-lg">{error}</div>}

                {/* Central Dashboard Card */}
                <div className="glass-card glass-highlight rounded-xl p-8 glow-primary relative overflow-hidden">
                    {/* Card Header Tabs */}
                    <div className="flex border-b border-white/10 mb-8 overflow-x-auto scrollbar-hide">
                        <button onClick={() => setActiveTab('text')} className={`px-6 py-4 text-lg transition-all flex items-center gap-2 whitespace-nowrap ${activeTab === 'text' ? 'text-primary border-b-2 border-primary' : 'text-on-surface-variant hover:text-on-surface border-b-2 border-transparent'}`}>
                            📝 Paste Text
                        </button>
                        <button onClick={() => setActiveTab('upload')} className={`px-6 py-4 text-lg transition-all flex items-center gap-2 whitespace-nowrap ${activeTab === 'upload' ? 'text-primary border-b-2 border-primary' : 'text-on-surface-variant hover:text-on-surface border-b-2 border-transparent'}`}>
                            📂 Upload Document
                        </button>
                        <button onClick={() => setActiveTab('academic')} className={`px-6 py-4 text-lg transition-all flex items-center gap-2 whitespace-nowrap ${activeTab === 'academic' ? 'text-primary border-b-2 border-primary' : 'text-on-surface-variant hover:text-on-surface border-b-2 border-transparent'}`}>
                            🎓 Academic Report
                        </button>
                    </div>

                    {/* Tab Content: Paste Text */}
                    {activeTab === 'text' && (
                        <div className="group relative">
                            <textarea value={text} onChange={e=>setText(e.target.value)} className="w-full h-80 bg-white/5 border border-white/10 rounded-lg p-6 text-on-surface placeholder:text-on-surface-variant/50 focus:ring-2 focus:ring-primary/50 focus:border-primary outline-none transition-all resize-none shadow-inner" placeholder="Paste your research notes, data, or draft here..."></textarea>
                            <div className="absolute inset-0 rounded-lg pointer-events-none group-focus-within:border-primary/30 border border-transparent transition-colors"></div>
                        </div>
                    )}

                    {/* Tab Content: Upload */}
                    {activeTab === 'upload' && (
                        <div className="w-full h-80 border-2 border-dashed border-white/20 rounded-lg flex flex-col items-center justify-center gap-4 hover:border-primary/50 transition-all cursor-pointer bg-white/[0.02] relative">
                            <input type="file" accept=".txt,.pdf,.docx" onChange={e=>setFile(e.target.files?.[0]||null)} className="absolute inset-0 opacity-0 cursor-pointer" />
                            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                                <span className="text-4xl text-primary">📄</span>
                            </div>
                            <div className="text-center">
                                <p className="text-xl text-on-surface">{file ? file.name : "Drag and drop your document"}</p>
                                <p className="text-md text-on-surface-variant mt-1">PDF, DOCX, or TXT</p>
                            </div>
                        </div>
                    )}

                    {/* Tab Content: Academic Report */}
                    {activeTab === 'academic' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-4">
                                <label className="block">
                                    <span className="text-xs text-on-surface-variant uppercase tracking-wider mb-2 block font-medium">Project ZIP</span>
                                    <input type="file" accept=".zip" onChange={e=>setProjZip(e.target.files?.[0]||null)} className="w-full bg-white/5 border border-white/10 rounded-lg p-2 text-sm text-on-surface focus:border-primary outline-none" />
                                </label>
                                <label className="block">
                                    <span className="text-xs text-on-surface-variant uppercase tracking-wider mb-2 block font-medium">GitHub URL</span>
                                    <input type="text" value={githubUrl} onChange={e=>setGithubUrl(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-on-surface focus:border-primary outline-none" placeholder="https://github.com/..." />
                                </label>
                                <label className="block">
                                    <span className="text-xs text-on-surface-variant uppercase tracking-wider mb-2 block font-medium">Team Members</span>
                                    <input type="text" value={teamMembersString} onChange={e=>setTeamMembersString(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-on-surface focus:border-primary outline-none" placeholder="John Doe, Jane Smith" />
                                </label>
                                <label className="block">
                                    <span className="text-xs text-on-surface-variant uppercase tracking-wider mb-2 block font-medium">Project Title</span>
                                    <input type="text" value={projTitle} onChange={e=>setProjTitle(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-on-surface focus:border-primary outline-none" placeholder="Autonomous Navigation Systems" />
                                </label>
                            </div>
                            <div className="space-y-4">
                                <label className="block">
                                    <span className="text-xs text-on-surface-variant uppercase tracking-wider mb-2 block font-medium">Degree & University</span>
                                    <div className="flex gap-2">
                                        <input type="text" value={degree} onChange={e=>setDegree(e.target.value)} className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-on-surface focus:border-primary outline-none" placeholder="B.Tech" />
                                        <input type="text" value={university} onChange={e=>setUniversity(e.target.value)} className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-on-surface focus:border-primary outline-none" placeholder="MIT" />
                                    </div>
                                </label>
                                <label className="block">
                                    <span className="text-xs text-on-surface-variant uppercase tracking-wider mb-2 block font-medium">Guide & HOD</span>
                                    <div className="flex gap-2">
                                        <input type="text" value={guide} onChange={e=>setGuide(e.target.value)} className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-on-surface focus:border-primary outline-none" placeholder="Dr. Alan" />
                                        <input type="text" value={hod} onChange={e=>setHod(e.target.value)} className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-on-surface focus:border-primary outline-none" placeholder="HOD Name" />
                                    </div>
                                </label>
                                <label className="block">
                                    <span className="text-xs text-on-surface-variant uppercase tracking-wider mb-2 block font-medium">Special Requests</span>
                                    <textarea value={specialRequestText} onChange={e=>setSpecialRequestText(e.target.value)} className="w-full h-28 bg-white/5 border border-white/10 rounded-lg p-4 text-on-surface focus:border-primary outline-none resize-none" placeholder="Add citations, custom styles, or specific focus areas..."></textarea>
                                </label>
                            </div>
                        </div>
                    )}

                    {/* Shared Controls Section */}
                    <div className="mt-8 pt-8 border-t border-white/10 space-y-6">
                        <div className="flex flex-col md:flex-row gap-6 items-end">
                            <div className="flex-1 w-full relative">
                                <span className="text-xs text-on-surface-variant uppercase tracking-wider mb-3 block font-medium">Attach Media</span>
                                <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
                                    <div className="w-24 h-24 rounded-lg glass-card flex-shrink-0 flex items-center justify-center group cursor-pointer hover:bg-white/10 transition-colors relative">
                                        <input type="file" multiple accept="image/*" onChange={e=>setImages(e.target.files)} className="absolute inset-0 opacity-0 cursor-pointer" />
                                        <span className="text-on-surface-variant text-2xl">📸</span>
                                    </div>
                                    {images && Array.from(images).map((img, idx) => (
                                       <div key={idx} className="w-24 h-24 rounded-lg bg-surface flex-shrink-0 border border-primary/50 flex items-center justify-center text-xs text-center p-2 text-primary break-all">{img.name}</div> 
                                    ))}
                                </div>
                            </div>
                            <div className="w-full md:w-64">
                                <span className="text-xs text-on-surface-variant uppercase tracking-wider mb-3 block font-medium">Placement</span>
                                <select value={imagePlacement} onChange={e=>setImagePlacement(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-on-surface focus:border-primary outline-none appearance-none cursor-pointer">
                                    <option className="bg-surface">Let AI Decide</option>
                                    <option className="bg-surface">Top</option>
                                    <option className="bg-surface">Bottom</option>
                                </select>
                            </div>
                        </div>

                        {/* Generate Button */}
                        <div className="pt-8">
                            <button onClick={()=>handleGenerate()} disabled={loading} className={`w-full py-6 rounded-full bg-gradient-to-r from-primary-container to-secondary-container text-white text-2xl font-bold flex items-center justify-center gap-3 shadow-[0_0_30px_rgba(79,70,229,0.4)] transition-all ${loading ? 'opacity-70 cursor-wait' : 'hover:shadow-[0_0_50px_rgba(79,70,229,0.6)] hover:scale-[1.02] active:scale-[0.98]'}`}>
                                <span>✨</span> {loading ? 'Processing Document...' : 'Generate Document'}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Footer Section */}
                <footer className="mt-16 flex flex-col md:flex-row justify-between items-center px-4 gap-4 opacity-60">
                    <p className="text-sm text-on-surface-variant">© 2026 WriteX Academic Engine. All rights reserved.</p>
                </footer>
            </div>
        </main>

        {/* Conflict Resolution Modal */}
        {showConflictModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
          <div className="glass-card rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto glow-primary border-primary/30">
            <h2 className="text-3xl font-bold text-error flex items-center gap-3 mb-2">
              ⚠️ Style Conflict Detected
            </h2>
            <p className="text-on-surface-variant text-md mb-8">
              Your "Special Requests" clash with the formatting rules found in your uploaded Inspiration File. Please select which rule to follow.
            </p>

            <div className="space-y-6">
              {conflicts.map((c, i) => {
                const isResolved = resolvedConflicts[c.parameter_key] !== undefined;
                return (
                  <div key={i} className={`p-5 rounded-xl border ${isResolved ? 'border-primary bg-primary/10' : 'border-white/10 bg-white/5'}`}>
                    <h3 className="font-bold text-lg text-on-surface mb-4">{c.parameter_label}</h3>
                    
                    {!isResolved ? (
                      <div className="space-y-3">
                        <button onClick={() => resolveConflict(c.parameter_key, c.reference_value)} className="w-full text-left p-4 rounded-lg bg-white/5 hover:bg-white/10 border border-transparent hover:border-white/20 transition-all">
                          <span className="block text-xs text-on-surface-variant uppercase tracking-wider mb-1 font-bold">Follow Reference File</span>
                          <span className="text-on-surface text-lg">{c.reference_value}</span>
                        </button>
                        <button onClick={() => resolveConflict(c.parameter_key, c.request_value)} className="w-full text-left p-4 rounded-lg bg-error-container/20 hover:bg-error-container/40 border border-transparent hover:border-error/50 transition-all">
                          <span className="block text-xs text-error uppercase tracking-wider mb-1 font-bold">Follow Special Request</span>
                          <span className="text-error text-lg">{c.request_value}</span>
                        </button>
                      </div>
                    ) : (
                      <div className="text-primary text-md flex items-center gap-3 font-medium">
                        <span>✅ Resolved to: <strong className="text-on-surface">{resolvedConflicts[c.parameter_key]}</strong></span>
                        <button onClick={() => {
                          const newRc = {...resolvedConflicts};
                          delete newRc[c.parameter_key];
                          setResolvedConflicts(newRc);
                        }} className="text-on-surface-variant hover:text-on-surface ml-auto underline text-sm">Undo</button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="mt-10 flex gap-4">
              <button onClick={() => { setShowConflictModal(false); setResolvedConflicts({}); setConflicts([]); }} className="flex-1 py-4 rounded-full border border-white/20 text-on-surface hover:bg-white/10 transition-colors font-bold">Cancel</button>
              <button onClick={() => handleGenerate(true)} disabled={Object.keys(resolvedConflicts).length !== conflicts.length} className="flex-1 py-4 rounded-full bg-primary text-on-primary font-bold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary-fixed transition-colors text-lg shadow-lg">Confirm & Generate</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
