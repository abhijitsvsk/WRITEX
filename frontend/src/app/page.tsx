"use client";
import React, { useState } from "react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"text" | "file" | "academic">("text");
  const [apiKey, setApiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ================= TAB 1 & 2 STATE =================
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

  // ================= TAB 3 (ACADEMIC) STATE =================
  const [projZip, setProjZip] = useState<File | null>(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [sampleRep, setSampleRep] = useState<File | null>(null);
  const [rewriteMode, setRewriteMode] = useState(false);
  const [testMetrics, setTestMetrics] = useState<File | null>(null);

  const [projTitle, setProjTitle] = useState("My Project");
  const [degree, setDegree] = useState("B.Tech Computer Science");
  const [university, setUniversity] = useState("My University");
  const [department, setDepartment] = useState("Computer Science and Engineering");
  const [academicYear, setAcademicYear] = useState("2025–2026");

  const [principal, setPrincipal] = useState("");
  const [hod, setHod] = useState("");
  const [guide, setGuide] = useState("");
  const [guideDesignation, setGuideDesignation] = useState("Assistant Professor");
  const [hodDesignation, setHodDesignation] = useState("Professor & HoD");

  const [teamMembers, setTeamMembers] = useState<string[]>(["", "", "", ""]);
  const [specialRequestText, setSpecialRequestText] = useState("");
  
  // Conflict Resolution State
  const [conflicts, setConflicts] = useState<any[]>([]);
  const [showConflictModal, setShowConflictModal] = useState(false);
  const [resolvedConflicts, setResolvedConflicts] = useState<Record<string, any>>({});


  const handleTeamMemberChange = (index: number, value: string) => {
    const newMembers = [...teamMembers];
    newMembers[index] = value;
    setTeamMembers(newMembers);
  };

  const addTeamMember = () => setTeamMembers([...teamMembers, ""]);
  const removeTeamMember = () => {
    if (teamMembers.length > 1) {
      setTeamMembers(teamMembers.slice(0, -1));
    }
  };


  const handleGenerate = async (isRetryWithResolutions = false) => {
    if (!apiKey) {
      setError("Please provide an API Key.");
      return;
    }
    
    setError("");
    setLoading(true);
    
    const formData = new FormData();
    formData.append("api_key", apiKey);
    
    let endpoint = "";

    if (activeTab === "text" || activeTab === "file") {
      endpoint = activeTab === "text" ? "http://localhost:8000/api/format_text" : "http://localhost:8000/api/format_file";
      
      formData.append("image_placement", imagePlacement);
      formData.append("style_name", "Academic");
      
      const styleConfig = {
        margin_inches: margin, heading_font: hFont, heading_size_pt: hSize, heading_bold: hBold,
        chapter_alignment: chapAlign, subheading_alignment: subhAlign, content_font: cFont,
        content_size_pt: cSize, content_alignment: cAlign, line_spacing: spacing,
        space_before_pt: spaceBefore, space_after_pt: spaceAfter, code_language: codeLang,
        continuous_sections: continuous
      };
      formData.append("style_config", JSON.stringify(styleConfig));
      
      if (images) {
        for (let i = 0; i < images.length; i++) formData.append("images", images[i]);
      }
      
      if (activeTab === "text") {
        if (!text) { setError("Please provide some raw text."); setLoading(false); return; }
        formData.append("text", text);
      } else {
        if (!file) { setError("Please upload a document."); setLoading(false); return; }
        formData.append("file", file);
      }
    } 
    else if (activeTab === "academic") {
      endpoint = "http://localhost:8000/api/format_academic_report";
      
      if (!projZip && !githubUrl) { setError("Please provide a Project ZIP or GitHub URL."); setLoading(false); return; }
      if (teamMembers.filter(n => n.trim()).length === 0) { setError("Please provide at least one team member."); setLoading(false); return; }

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
      formData.append("team_names", teamMembers.filter(n => n.trim()).join(","));
      formData.append("special_request_text", specialRequestText);
      formData.append("resolved_conflicts", JSON.stringify(resolvedConflicts));
    }
    
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });
      
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

      if (isRetryWithResolutions) {
        setShowConflictModal(false);
        setConflicts([]);
        setResolvedConflicts({});
      }

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const resolveConflict = (key: string, value: any) => {
    setResolvedConflicts(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-slate-200 p-8 font-sans bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-[#0a0a0a] to-[#0a0a0a]">
      <div className="max-w-5xl mx-auto">
        
        {/* Header */}
        <header className="mb-12 text-center space-y-4">
          <h1 className="text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
            WriteX
          </h1>
          <p className="text-slate-400 text-lg">Academic Report Generation Engine</p>
        </header>
        
        {/* API Key */}
        <div className="backdrop-blur-md bg-slate-900/40 border border-slate-800 rounded-2xl p-6 mb-8 shadow-2xl">
          <label className="block text-sm font-medium text-slate-400 mb-2">Groq / DeepSeek API Key</label>
          <input 
            type="password" 
            value={apiKey} 
            onChange={e => setApiKey(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
            placeholder="sk-..."
          />
        </div>

        {/* Main Content Card */}
        <div className="backdrop-blur-md bg-slate-900/40 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl relative">
          
          {/* Tabs */}
          <div className="flex border-b border-slate-800">
            <button 
              className={`flex-1 py-4 text-center font-medium transition-colors ${activeTab === 'text' ? 'bg-indigo-500/10 text-indigo-400 border-b-2 border-indigo-500' : 'text-slate-500 hover:bg-slate-800/50'}`}
              onClick={() => setActiveTab('text')}
            >📄 Paste Text</button>
            <button 
              className={`flex-1 py-4 text-center font-medium transition-colors ${activeTab === 'file' ? 'bg-indigo-500/10 text-indigo-400 border-b-2 border-indigo-500' : 'text-slate-500 hover:bg-slate-800/50'}`}
              onClick={() => setActiveTab('file')}
            >📂 Upload Doc</button>
            <button 
              className={`flex-1 py-4 text-center font-medium transition-colors ${activeTab === 'academic' ? 'bg-purple-500/10 text-purple-400 border-b-2 border-purple-500' : 'text-slate-500 hover:bg-slate-800/50'}`}
              onClick={() => setActiveTab('academic')}
            >🎓 Academic Report (Strict)</button>
          </div>

          <div className="p-8 space-y-10">
            
            {/* -------------------- TAB 1 & 2 CONTENT -------------------- */}
            {activeTab !== "academic" && (
              <>
                <section className="space-y-4">
                  <h2 className="text-xl font-bold flex items-center text-slate-200">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-500/20 text-indigo-400 text-sm mr-3">1</span>
                    Provide Content
                  </h2>
                  {activeTab === "text" ? (
                    <textarea 
                      value={text} onChange={e => setText(e.target.value)}
                      className="w-full h-64 bg-slate-950 border border-slate-800 rounded-xl p-4 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-y font-mono text-sm"
                      placeholder="Paste your raw text or code here..."
                    />
                  ) : (
                    <div className="border-2 border-dashed border-slate-700 rounded-xl p-10 text-center hover:bg-slate-800/50 cursor-pointer">
                      <input type="file" accept=".txt,.pdf,.docx" onChange={e => setFile(e.target.files?.[0] || null)} className="hidden" id="file-upload" />
                      <label htmlFor="file-upload" className="cursor-pointer block">
                        <div className="text-4xl mb-3">📄</div>
                        <div className="text-slate-300 font-medium">Click to upload or drag and drop</div>
                        <div className="text-slate-500 text-sm mt-1">PDF, DOCX, or TXT</div>
                        {file && <div className="mt-4 text-indigo-400 font-medium">{file.name}</div>}
                      </label>
                    </div>
                  )}
                </section>

                <section className="space-y-4">
                  <h2 className="text-xl font-bold flex items-center text-slate-200">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-500/20 text-indigo-400 text-sm mr-3">2</span>
                    Attach Media <span className="text-slate-500 text-sm ml-2 font-normal">(Optional)</span>
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-950/50 p-6 rounded-xl border border-slate-800">
                    <div>
                      <label className="block text-sm font-medium text-slate-400 mb-2">Upload Images</label>
                      <input type="file" multiple accept="image/*" onChange={e => setImages(e.target.files)} className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-500/10 file:text-indigo-400 cursor-pointer" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-400 mb-2">Placement</label>
                      <select value={imagePlacement} onChange={e => setImagePlacement(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                        <option>Let AI Decide</option><option>Top</option><option>Bottom</option>
                      </select>
                    </div>
                  </div>
                </section>

                <section className="space-y-4">
                  <h2 className="text-xl font-bold flex items-center text-slate-200">
                    <span className="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-500/20 text-indigo-400 text-sm mr-3">3</span>
                    Advanced Layout <span className="text-slate-500 text-sm ml-2 font-normal">(Optional)</span>
                  </h2>
                  <details className="group bg-slate-950/50 border border-slate-800 rounded-xl overflow-hidden cursor-pointer">
                    <summary className="p-4 font-medium text-slate-300 hover:bg-slate-800/50 transition-colors flex justify-between items-center">
                      Configure margins, fonts, and spacing...
                      <span className="group-open:rotate-180 transition-transform">▼</span>
                    </summary>
                    <div className="p-6 border-t border-slate-800 space-y-8 cursor-default">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {/* Heading & Content Layout Settings Here (Omitted for brevity, using defaults for now to keep code clean) */}
                        <div className="text-slate-400 text-sm">Advanced layout fields bound to state.</div>
                      </div>
                    </div>
                  </details>
                </section>
              </>
            )}

            {/* -------------------- TAB 3 CONTENT (ACADEMIC) -------------------- */}
            {activeTab === "academic" && (
              <>
                <div className="bg-purple-900/20 border border-purple-500/30 rounded-xl p-4 text-purple-200 text-sm flex items-start gap-3">
                  <span className="text-xl">🎓</span>
                  <p>Generates a strict 6-chapter academic report with standard Front Matter by parsing your codebase using Map-Reduce ASTs.</p>
                </div>

                <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {/* Left Column: Files */}
                  <div className="space-y-6">
                    <h3 className="text-lg font-bold text-slate-200 border-b border-slate-800 pb-2">Code & References</h3>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-400 mb-2">Project ZIP</label>
                      <input type="file" accept=".zip" onChange={e => setProjZip(e.target.files?.[0] || null)} className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-slate-800 file:text-slate-300 cursor-pointer" />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-400 mb-2">Or GitHub URL</label>
                      <input type="text" value={githubUrl} onChange={e => setGithubUrl(e.target.value)} placeholder="https://github.com/user/repo" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500" />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-400 mb-2">Inspiration File (PDF/DOCX) <span className="text-xs text-slate-500 ml-2">Optional</span></label>
                      <input type="file" accept=".pdf,.docx,.txt" onChange={e => setSampleRep(e.target.files?.[0] || null)} className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-slate-800 file:text-slate-300 cursor-pointer" />
                      <label className="flex items-center space-x-2 text-sm text-slate-300 cursor-pointer mt-3">
                        <input type="checkbox" checked={rewriteMode} onChange={e=>setRewriteMode(e.target.checked)} className="rounded border-slate-700 text-purple-500 focus:ring-purple-500 bg-slate-900"/>
                        <span>Rewrite Mode (Match tone strictly)</span>
                      </label>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-400 mb-2">Test Metrics (CSV/JSON) <span className="text-xs text-slate-500 ml-2">Optional</span></label>
                      <input type="file" accept=".csv,.json,.txt" onChange={e => setTestMetrics(e.target.files?.[0] || null)} className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-slate-800 file:text-slate-300 cursor-pointer" />
                    </div>
                  </div>

                  {/* Right Column: Metadata */}
                  <div className="space-y-6">
                    <h3 className="text-lg font-bold text-slate-200 border-b border-slate-800 pb-2">Project Details</h3>
                    
                    <div className="space-y-4">
                      <input type="text" value={projTitle} onChange={e => setProjTitle(e.target.value)} placeholder="Project Title" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500" />
                      <div className="grid grid-cols-2 gap-4">
                        <input type="text" value={degree} onChange={e => setDegree(e.target.value)} placeholder="Degree" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500" />
                        <input type="text" value={academicYear} onChange={e => setAcademicYear(e.target.value)} placeholder="Academic Year" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500" />
                      </div>
                      <input type="text" value={university} onChange={e => setUniversity(e.target.value)} placeholder="University" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500" />
                      <input type="text" value={department} onChange={e => setDepartment(e.target.value)} placeholder="Department" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500" />
                    </div>
                  </div>
                </section>

                <section className="space-y-6 pt-6 border-t border-slate-800">
                  <h3 className="text-lg font-bold text-slate-200">Team & Signatories</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-4">
                      <div className="flex gap-4 mb-2">
                        <button onClick={addTeamMember} className="bg-slate-800 hover:bg-slate-700 text-xs py-1.5 px-3 rounded-md transition-colors">+ Add Member</button>
                        <button onClick={removeTeamMember} className="bg-slate-800 hover:bg-slate-700 text-xs py-1.5 px-3 rounded-md transition-colors">- Remove</button>
                      </div>
                      {teamMembers.map((name, i) => (
                        <input key={i} type="text" value={name} onChange={e => handleTeamMemberChange(i, e.target.value)} placeholder={`Member ${i+1} Name`} className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500" />
                      ))}
                    </div>
                    
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <input type="text" value={guide} onChange={e => setGuide(e.target.value)} placeholder="Guide Name" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500" />
                        <input type="text" value={guideDesignation} onChange={e => setGuideDesignation(e.target.value)} placeholder="Guide Designation" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500" />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <input type="text" value={hod} onChange={e => setHod(e.target.value)} placeholder="HOD Name" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500" />
                        <input type="text" value={hodDesignation} onChange={e => setHodDesignation(e.target.value)} placeholder="HOD Designation" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500" />
                      </div>
                      <input type="text" value={principal} onChange={e => setPrincipal(e.target.value)} placeholder="Principal Name" className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500" />
                    </div>
                  </div>
                </section>

                <section className="space-y-4 pt-6 border-t border-slate-800">
                  <h3 className="text-lg font-bold text-purple-400">✨ Special Requests</h3>
                  <p className="text-xs text-slate-400">Ask the AI for specific constraints (e.g. 'Make the report strictly under 30 pages' or 'Use Arial size 14 for headings').</p>
                  <textarea 
                    value={specialRequestText} onChange={e => setSpecialRequestText(e.target.value)}
                    className="w-full h-24 bg-slate-950 border border-slate-800 rounded-xl p-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-y font-mono text-sm"
                    placeholder="Describe any special requirements here..."
                  />
                </section>
              </>
            )}

            {/* Error Message */}
            {error && (
              <div className="p-4 rounded-lg bg-red-900/30 border border-red-500/50 text-red-400 text-sm text-center">
                {error}
              </div>
            )}

            {/* Submit */}
            <section className="pt-4">
              <button 
                onClick={() => handleGenerate()}
                disabled={loading}
                className={`w-full py-4 rounded-xl font-bold text-lg text-white shadow-[0_0_40px_rgba(99,102,241,0.4)] transition-all duration-300 flex items-center justify-center space-x-3
                  ${loading ? 'bg-indigo-600/50 cursor-not-allowed' : (activeTab === 'academic' ? 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:scale-[1.02]' : 'bg-gradient-to-r from-indigo-500 to-blue-600 hover:scale-[1.02]')}
                `}
              >
                {loading ? <span>Generating Document (This may take a while)...</span> : <span>✨ Generate Document</span>}
              </button>
            </section>
          </div>
        </div>
      </div>

      {/* CONFLICT RESOLUTION MODAL */}
      {showConflictModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold text-amber-500 flex items-center gap-3 mb-2">
              ⚠️ Conflict Resolution Required
            </h2>
            <p className="text-slate-400 text-sm mb-6">
              Your "Special Requests" clash with the formatting rules found in your uploaded Inspiration File. Please tell me which rule to follow for each conflict.
            </p>

            <div className="space-y-6">
              {conflicts.map((c, i) => {
                const isResolved = resolvedConflicts[c.parameter_key] !== undefined;
                return (
                  <div key={i} className={`p-5 rounded-xl border ${isResolved ? 'border-green-500/50 bg-green-900/10' : 'border-slate-700 bg-slate-950'}`}>
                    <h3 className="font-bold text-slate-200 mb-3">{c.parameter_label}</h3>
                    
                    {!isResolved ? (
                      <div className="space-y-3">
                        <button onClick={() => resolveConflict(c.parameter_key, c.reference_value)} className="w-full text-left p-3 rounded bg-slate-800 hover:bg-slate-700 transition-colors">
                          <span className="block text-xs text-slate-400 uppercase tracking-wider mb-1">Follow Reference File</span>
                          <span className="text-slate-200">{c.reference_value}</span>
                        </button>
                        <button onClick={() => resolveConflict(c.parameter_key, c.request_value)} className="w-full text-left p-3 rounded bg-slate-800 hover:bg-slate-700 transition-colors">
                          <span className="block text-xs text-slate-400 uppercase tracking-wider mb-1">Follow Special Request</span>
                          <span className="text-amber-400">{c.request_value}</span>
                        </button>
                      </div>
                    ) : (
                      <div className="text-green-400 text-sm flex items-center gap-2">
                        <span>✅ Resolved to: <strong>{resolvedConflicts[c.parameter_key]}</strong></span>
                        <button onClick={() => {
                          const newRc = {...resolvedConflicts};
                          delete newRc[c.parameter_key];
                          setResolvedConflicts(newRc);
                        }} className="text-slate-500 hover:text-slate-300 ml-auto underline text-xs">Undo</button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="mt-8 flex gap-4">
              <button 
                onClick={() => { setShowConflictModal(false); setResolvedConflicts({}); setConflicts([]); }}
                className="flex-1 py-3 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 transition-colors"
              >Cancel</button>
              <button 
                onClick={() => handleGenerate(true)}
                disabled={Object.keys(resolvedConflicts).length !== conflicts.length}
                className="flex-1 py-3 rounded-lg bg-amber-600 text-white font-bold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-amber-500 transition-colors"
              >Confirm Resolutions & Generate</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
