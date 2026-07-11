"use client";
import React, { useState } from "react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"text" | "file">("text");
  const [apiKey, setApiKey] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [images, setImages] = useState<FileList | null>(null);
  const [imagePlacement, setImagePlacement] = useState("Let AI Decide");
  
  // Advanced Layout State
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
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!apiKey) {
      setError("Please provide an API Key.");
      return;
    }
    
    setError("");
    setLoading(true);
    
    const formData = new FormData();
    formData.append("api_key", apiKey);
    formData.append("image_placement", imagePlacement);
    formData.append("style_name", "Academic");
    
    const styleConfig = {
      margin_inches: margin,
      heading_font: hFont,
      heading_size_pt: hSize,
      heading_bold: hBold,
      chapter_alignment: chapAlign,
      subheading_alignment: subhAlign,
      content_font: cFont,
      content_size_pt: cSize,
      content_alignment: cAlign,
      line_spacing: spacing,
      space_before_pt: spaceBefore,
      space_after_pt: spaceAfter,
      code_language: codeLang,
      continuous_sections: continuous
    };
    
    formData.append("style_config", JSON.stringify(styleConfig));
    
    if (images) {
      for (let i = 0; i < images.length; i++) {
        formData.append("images", images[i]);
      }
    }
    
    let endpoint = "http://localhost:8000/api/format_text";
    if (activeTab === "text") {
      if (!text) {
        setError("Please provide some raw text.");
        setLoading(false);
        return;
      }
      formData.append("text", text);
    } else {
      if (!file) {
        setError("Please upload a document.");
        setLoading(false);
        return;
      }
      formData.append("file", file);
      endpoint = "http://localhost:8000/api/format_file";
    }
    
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Generation failed.");
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = activeTab === "text" ? "formatted.docx" : "formatted_file.docx";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-slate-200 p-8 font-sans bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-[#0a0a0a] to-[#0a0a0a]">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <header className="mb-12 text-center space-y-4">
          <h1 className="text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500">
            WriteX
          </h1>
          <p className="text-slate-400 text-lg">Academic Report Generation Engine</p>
        </header>
        
        {/* API Key */}
        <div className="backdrop-blur-md bg-slate-900/40 border border-slate-800 rounded-2xl p-6 mb-8 shadow-2xl transition-all duration-300 hover:border-slate-700">
          <label className="block text-sm font-medium text-slate-400 mb-2">Groq / DeepSeek API Key</label>
          <input 
            type="password" 
            value={apiKey} 
            onChange={e => setApiKey(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
            placeholder="sk-..."
          />
        </div>

        {/* Main Content Card */}
        <div className="backdrop-blur-md bg-slate-900/40 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
          
          {/* Tabs */}
          <div className="flex border-b border-slate-800">
            <button 
              className={`flex-1 py-4 text-center font-medium transition-colors ${activeTab === 'text' ? 'bg-indigo-500/10 text-indigo-400 border-b-2 border-indigo-500' : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'}`}
              onClick={() => setActiveTab('text')}
            >
              📄 Paste Text
            </button>
            <button 
              className={`flex-1 py-4 text-center font-medium transition-colors ${activeTab === 'file' ? 'bg-indigo-500/10 text-indigo-400 border-b-2 border-indigo-500' : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'}`}
              onClick={() => setActiveTab('file')}
            >
              📂 Upload Document
            </button>
          </div>

          <div className="p-8 space-y-10">
            
            {/* Step 1: Content */}
            <section className="space-y-4">
              <h2 className="text-xl font-bold flex items-center text-slate-200">
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-500/20 text-indigo-400 text-sm mr-3">1</span>
                Provide Content
              </h2>
              {activeTab === "text" ? (
                <textarea 
                  value={text}
                  onChange={e => setText(e.target.value)}
                  className="w-full h-64 bg-slate-950 border border-slate-800 rounded-xl p-4 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-y font-mono text-sm"
                  placeholder="Paste your raw text or code here..."
                />
              ) : (
                <div className="border-2 border-dashed border-slate-700 rounded-xl p-10 text-center hover:bg-slate-800/50 hover:border-slate-600 transition-all cursor-pointer">
                  <input 
                    type="file" 
                    accept=".txt,.pdf,.docx" 
                    onChange={e => setFile(e.target.files?.[0] || null)}
                    className="hidden" 
                    id="file-upload" 
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <div className="text-4xl mb-3">📄</div>
                    <div className="text-slate-300 font-medium">Click to upload or drag and drop</div>
                    <div className="text-slate-500 text-sm mt-1">PDF, DOCX, or TXT</div>
                    {file && <div className="mt-4 text-indigo-400 font-medium">{file.name}</div>}
                  </label>
                </div>
              )}
            </section>

            {/* Step 2: Media */}
            <section className="space-y-4">
              <h2 className="text-xl font-bold flex items-center text-slate-200">
                <span className="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-500/20 text-indigo-400 text-sm mr-3">2</span>
                Attach Media <span className="text-slate-500 text-sm ml-2 font-normal">(Optional)</span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-950/50 p-6 rounded-xl border border-slate-800">
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">Upload Images</label>
                  <input 
                    type="file" 
                    multiple 
                    accept="image/*"
                    onChange={e => setImages(e.target.files)}
                    className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-500/10 file:text-indigo-400 hover:file:bg-indigo-500/20 cursor-pointer"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">Placement</label>
                  <select 
                    value={imagePlacement}
                    onChange={e => setImagePlacement(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option>Let AI Decide</option>
                    <option>Top</option>
                    <option>Bottom</option>
                  </select>
                </div>
              </div>
            </section>

            {/* Step 3: Layout */}
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
                  {/* Grid Layouts */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    
                    {/* Headings */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-bold tracking-wider text-indigo-400 uppercase">Headings</h3>
                      
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Font Family</label>
                          <select value={hFont} onChange={e=>setHFont(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200">
                            <option>Times New Roman</option><option>Arial</option><option>Calibri</option><option>Courier New</option>
                          </select>
                        </div>
                        <div className="flex gap-4">
                          <div className="flex-1">
                            <label className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Size (pt)</label>
                            <input type="number" value={hSize} onChange={e=>setHSize(Number(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200"/>
                          </div>
                          <div className="flex-1 flex items-end pb-2">
                            <label className="flex items-center space-x-2 text-sm text-slate-300 cursor-pointer">
                              <input type="checkbox" checked={hBold} onChange={e=>setHBold(e.target.checked)} className="rounded border-slate-700 text-indigo-500 focus:ring-indigo-500 bg-slate-900"/>
                              <span>Bold</span>
                            </label>
                          </div>
                        </div>
                        <div>
                          <label className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Chapter Alignment</label>
                          <select value={chapAlign} onChange={e=>setChapAlign(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200">
                            <option>Left</option><option>Center</option><option>Right</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Sub-heading Alignment</label>
                          <select value={subhAlign} onChange={e=>setSubhAlign(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200">
                            <option>Left</option><option>Center</option><option>Right</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Content */}
                    <div className="space-y-4">
                      <h3 className="text-sm font-bold tracking-wider text-indigo-400 uppercase">Content & Spacing</h3>
                      
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Font Family</label>
                          <select value={cFont} onChange={e=>setCFont(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200">
                            <option>Times New Roman</option><option>Arial</option><option>Calibri</option><option>Courier New</option>
                          </select>
                        </div>
                        <div className="flex gap-4">
                          <div className="flex-1">
                            <label className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Size (pt)</label>
                            <input type="number" value={cSize} onChange={e=>setCSize(Number(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200"/>
                          </div>
                          <div className="flex-1">
                            <label className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Line Spacing</label>
                            <input type="number" step="0.25" value={spacing} onChange={e=>setSpacing(Number(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200"/>
                          </div>
                        </div>
                        <div className="flex gap-4">
                          <div className="flex-1">
                            <label className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Margins (in)</label>
                            <input type="number" step="0.25" value={margin} onChange={e=>setMargin(Number(e.target.value))} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200"/>
                          </div>
                          <div className="flex-1">
                            <label className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Alignment</label>
                            <select value={cAlign} onChange={e=>setCAlign(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200">
                              <option>Justify</option><option>Left</option><option>Center</option><option>Right</option>
                            </select>
                          </div>
                        </div>
                        <div>
                          <label className="flex items-center space-x-2 text-sm text-slate-300 cursor-pointer pt-3">
                            <input type="checkbox" checked={continuous} onChange={e=>setContinuous(e.target.checked)} className="rounded border-slate-700 text-indigo-500 focus:ring-indigo-500 bg-slate-900"/>
                            <span>Continuous Sections (No Page Breaks)</span>
                          </label>
                        </div>
                      </div>
                    </div>
                    
                  </div>
                </div>
              </details>
            </section>

            {/* Error Message */}
            {error && (
              <div className="p-4 rounded-lg bg-red-900/30 border border-red-500/50 text-red-400 text-sm text-center">
                {error}
              </div>
            )}

            {/* Step 4: Submit */}
            <section className="pt-4">
              <button 
                onClick={handleGenerate}
                disabled={loading}
                className={`w-full py-4 rounded-xl font-bold text-lg text-white shadow-[0_0_40px_rgba(99,102,241,0.4)] transition-all duration-300 flex items-center justify-center space-x-3
                  ${loading ? 'bg-indigo-600/50 cursor-not-allowed' : 'bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-400 hover:to-blue-500 hover:scale-[1.02] hover:shadow-[0_0_60px_rgba(99,102,241,0.6)]'}
                `}
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    <span>Generating Document...</span>
                  </>
                ) : (
                  <span>✨ Generate Document</span>
                )}
              </button>
            </section>

          </div>
        </div>
        
      </div>
    </div>
  );
}
