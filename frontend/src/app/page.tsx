"use client";
import React, { useState, CSSProperties } from "react";

// ─── Design Tokens ────────────────────────────────────────────────────────────
const C = {
  bgBase:     "#09090b",
  bgSurface:  "#0f0f12",
  bgElevated: "#141418",
  bgOverlay:  "#1a1a20",
  bgSubtle:   "#222228",

  borderFaint:  "rgba(255,255,255,0.05)",
  borderSubtle: "rgba(255,255,255,0.08)",
  borderDef:    "rgba(255,255,255,0.12)",
  borderStr:    "rgba(255,255,255,0.20)",

  accent:     "#6366f1",
  accentHov:  "#818cf8",
  accentDim:  "rgba(99,102,241,0.12)",
  accentGlow: "rgba(99,102,241,0.3)",

  textPri:  "#f4f4f5",
  textSec:  "#a1a1aa",
  textTer:  "#71717a",
  textMuted:"#52525b",

  success: "#22c55e",
  successDim: "rgba(34,197,94,0.12)",
  error:   "#ef4444",
  errorDim: "rgba(239,68,68,0.1)",
  warn:    "#f59e0b",
};

// ─── Micro-helpers ────────────────────────────────────────────────────────────
const Icon = ({ name, size = 16, color, style }: { name: string; size?: number; color?: string; style?: CSSProperties }) => (
  <span
    className="material-symbols-outlined"
    style={{ fontSize: size, color: color ?? "inherit", lineHeight: 1, display: "inline-block", verticalAlign: "middle", flexShrink: 0, ...style }}
  >
    {name}
  </span>
);

const Label = ({ children }: { children: React.ReactNode }) => (
  <span style={{ fontSize: 10.5, fontWeight: 600, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.09em", fontFamily: "'JetBrains Mono', monospace", display: "block", marginBottom: 6 }}>
    {children}
  </span>
);

const Input = ({
  value, onChange, placeholder, type = "text", mono = false, style,
}: {
  value: string | number;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
  mono?: boolean;
  style?: CSSProperties;
}) => {
  const [focused, setFocused] = useState(false);
  return (
    <input
      type={type}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      style={{
        width: "100%",
        background: C.bgOverlay,
        border: `1px solid ${focused ? C.accent : C.borderDef}`,
        borderRadius: 8,
        padding: "8px 12px",
        fontSize: mono ? 12 : 13,
        fontFamily: mono ? "'JetBrains Mono', monospace" : "'Inter', sans-serif",
        color: C.textPri,
        outline: "none",
        boxShadow: focused ? `0 0 0 3px ${C.accentDim}` : "none",
        transition: "border-color 0.15s, box-shadow 0.15s",
        boxSizing: "border-box",
        ...style,
      }}
    />
  );
};

const Select = ({ value, onChange, options, style }: { value: string; onChange: (v: string) => void; options: string[]; style?: CSSProperties }) => {
  const [focused, setFocused] = useState(false);
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      style={{
        width: "100%",
        background: C.bgOverlay,
        border: `1px solid ${focused ? C.accent : C.borderDef}`,
        borderRadius: 8,
        padding: "8px 10px",
        fontSize: 12,
        fontFamily: "'Inter', sans-serif",
        color: C.textPri,
        outline: "none",
        boxShadow: focused ? `0 0 0 3px ${C.accentDim}` : "none",
        transition: "border-color 0.15s, box-shadow 0.15s",
        cursor: "pointer",
        appearance: "none" as const,
        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`,
        backgroundRepeat: "no-repeat",
        backgroundPosition: "right 10px center",
        paddingRight: 28,
        ...style,
      }}
    >
      {options.map(o => <option key={o} value={o} style={{ background: C.bgOverlay }}>{o}</option>)}
    </select>
  );
};

const SectionCard = ({ title, right, children }: { title: string; right?: React.ReactNode; children: React.ReactNode }) => (
  <div style={{ background: C.bgElevated, border: `1px solid ${C.borderSubtle}`, borderRadius: 12, overflow: "hidden" }}>
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "10px 16px", borderBottom: `1px solid ${C.borderFaint}`,
      background: "rgba(255,255,255,0.015)",
    }}>
      <span style={{ fontSize: 10.5, fontWeight: 600, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.09em", fontFamily: "'JetBrains Mono', monospace" }}>{title}</span>
      {right}
    </div>
    <div style={{ padding: 16 }}>{children}</div>
  </div>
);

interface Conflict {
  parameter_key: string;
  parameter_label: string;
  reference_value: string;
  request_value: string;
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function Home() {
  const [activeTab, setActiveTab] = useState<"text"|"upload"|"academic">("text");
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState<"groq"|"deepseek">("groq");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [text, setText] = useState("");
  const [file, setFile] = useState<File|null>(null);
  const [hFont, setHFont] = useState("Times New Roman");
  const [hSize, setHSize] = useState("14");
  const [spacing, setSpacing] = useState("1.5");
  const [margin, setMargin] = useState("25");
  const [cAlign, setCAlign] = useState("Justify");
  const [codeLang, setCodeLang] = useState("Auto");
  const [images, setImages] = useState<File[]>([]);
  const [imagePlacement, setImagePlacement] = useState("Let AI Decide");
  const [highlightCode, setHighlightCode] = useState(true);
  const [autoNumbering, setAutoNumbering] = useState(false);
  const [continuousSections, setContinuousSections] = useState(true);

  const [projZip, setProjZip] = useState<File|null>(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [projTitle, setProjTitle] = useState("");
  const [degree, setDegree] = useState("");
  const [university, setUniversity] = useState("");
  const [dept, setDept] = useState("");
  const [acYear, setAcYear] = useState("");
  const [principal, setPrincipal] = useState("");
  const [guide, setGuide] = useState("");
  const [guideDesig, setGuideDesig] = useState("");
  const [hod, setHod] = useState("");
  const [hodDesig, setHodDesig] = useState("");
  const [teamMembers, setTeamMembers] = useState<string[]>([""]);

  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [showConflict, setShowConflict] = useState(false);
  const [resolved, setResolved] = useState<Record<string, string>>({});

  const [apiFocused, setApiFocused] = useState(false);

  const handleGenerate = async (isRetry = false) => {
    if (!apiKey.trim()) { setError("Enter your API key in the top bar."); return; }
    setError(""); setLoading(true);
    const fd = new FormData();
    fd.append("api_key", apiKey);
    fd.append("provider", provider);
    let endpoint = "";

    if (activeTab !== "academic") {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      endpoint = activeTab === "text" ? `${baseUrl}/api/format_text` : `${baseUrl}/api/format_file`;
      fd.append("style_name", "Academic");
      fd.append("style_config", JSON.stringify({
        margin_inches: +margin / 25.4, heading_font: hFont, heading_size_pt: +hSize,
        heading_bold: true, chapter_alignment: cAlign, subheading_alignment: cAlign,
        content_font: "Times New Roman", content_size_pt: 12, content_alignment: cAlign,
        line_spacing: +spacing, space_before_pt: 0, space_after_pt: 0,
        code_language: codeLang, highlight_code: highlightCode, continuous_sections: continuousSections,
        auto_numbering: autoNumbering
      }));
      fd.append("image_placement", imagePlacement);
      if (images && images.length > 0) {
        images.forEach(img => fd.append("images", img));
      }
      if (activeTab === "text") {
        if (!text.trim()) { setError("Paste some text first."); setLoading(false); return; }
        fd.append("text", text);
      } else {
        if (!file) { setError("Upload a document first."); setLoading(false); return; }
        if (file.size > 50 * 1024 * 1024) { setError("File is too large (max 50MB)."); setLoading(false); return; }
        fd.append("file", file);
      }
    } else {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      endpoint = `${baseUrl}/api/format_academic_report`;
      if (!projZip && !githubUrl.trim()) { setError("Provide a ZIP or GitHub URL."); setLoading(false); return; }
      if (projZip && projZip.size > 50 * 1024 * 1024) { setError("ZIP is too large (max 50MB)."); setLoading(false); return; }
      if (projZip) fd.append("proj_zip", projZip);
      fd.append("github_url", githubUrl); fd.append("rewrite_mode", "false");
      fd.append("title", projTitle); fd.append("degree", degree);
      fd.append("university", university); fd.append("department", dept);
      fd.append("academic_year", acYear); fd.append("principal", principal);
      fd.append("hod", hod); fd.append("guide", guide);
      fd.append("guide_designation", guideDesig); fd.append("hod_designation", hodDesig);
      fd.append("team_names", teamMembers.filter(n => n.trim()).join(","));
      fd.append("resolved_conflicts", JSON.stringify(resolved));
    }

    try {
      const res = await fetch(endpoint, { method: "POST", body: fd });
      if (res.status === 409) {
        const d = await res.json(); setConflicts(d.conflicts); setShowConflict(true); setLoading(false); return;
      }
      if (!res.ok) {
        const contentType = res.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const e = await res.json();
          throw new Error(e.detail || "Generation failed.");
        } else {
          throw new Error(`The server took too long to respond or threw a fatal error (HTTP ${res.status}).`);
        }
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url;
      a.download = activeTab === "academic" ? "Academic_Report.docx" : "formatted.docx";
      a.click(); URL.revokeObjectURL(url);
      if (isRetry) { setShowConflict(false); setConflicts([]); setResolved({}); }
    } catch(e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally { setLoading(false); }
  };

  const tabs = [
    { id: "text" as const, label: "Paste Text", icon: "content_paste" },
    { id: "upload" as const, label: "Upload Document", icon: "upload_file" },
    { id: "academic" as const, label: "Academic Report", icon: "school" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: C.bgBase, fontFamily: "'Inter', -apple-system, sans-serif" }}>

      {/* ─── NAV ─── */}
      <nav style={{
        position: "fixed", top: 0, left: 0, right: 0, zIndex: 50,
        height: 52, display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "0 24px",
        background: "rgba(9,9,11,0.8)",
        backdropFilter: "blur(20px)",
        borderBottom: `1px solid ${C.borderFaint}`,
      }}>
        {/* Left: Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{
            fontSize: 17, fontWeight: 800, letterSpacing: "-0.6px",
            background: "linear-gradient(135deg, #a5b4fc 0%, #818cf8 50%, #c4b5fd 100%)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          }}>WriteX</span>
          <span style={{ width: 1, height: 18, background: C.borderDef }} />
          <span style={{ fontSize: 12, color: C.textMuted, fontWeight: 500 }}>Academic AI Writer</span>
        </div>

        {/* Right: Provider toggle + API Key + Account */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>

          {/* Provider toggle pill */}
          <div style={{
            display: "flex",
            background: C.bgOverlay,
            border: `1px solid ${C.borderDef}`,
            borderRadius: 9,
            overflow: "hidden",
            height: 34,
          }}>
            {(["groq", "deepseek"] as const).map((p) => {
              const active = provider === p;
              const labels: Record<string, string> = { groq: "Groq", deepseek: "DeepSeek" };
              const icons:  Record<string, string> = { groq: "bolt", deepseek: "psychology" };
              return (
                <button
                  key={p}
                  onClick={() => setProvider(p)}
                  style={{
                    display: "flex", alignItems: "center", gap: 6,
                    padding: "0 14px", height: "100%",
                    background: active ? C.accentDim : "transparent",
                    border: "none",
                    borderRight: p === "groq" ? `1px solid ${C.borderDef}` : "none",
                    color: active ? C.accent : C.textMuted,
                    fontSize: 12, fontWeight: active ? 600 : 500,
                    cursor: "pointer",
                    transition: "background 0.15s, color 0.15s",
                    fontFamily: "'Inter', sans-serif",
                  }}
                >
                  <Icon name={icons[p]} size={13} color={active ? C.accent : C.textMuted} />
                  {labels[p]}
                </button>
              );
            })}
          </div>

          {/* API Key input */}
          <div style={{
            display: "flex", alignItems: "center", gap: 8,
            background: C.bgElevated,
            border: `1px solid ${apiFocused ? C.accent : C.borderDef}`,
            borderRadius: 9,
            padding: "0 12px", height: 34,
            boxShadow: apiFocused ? `0 0 0 3px ${C.accentDim}` : "none",
            transition: "border-color 0.15s, box-shadow 0.15s",
          }}>
            <Icon name="key" size={14} color={C.textMuted} />
            <input
              type="password"
              placeholder={provider === "groq" ? "gsk_…" : "sk-…"}
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              onFocus={() => setApiFocused(true)}
              onBlur={() => setApiFocused(false)}
              style={{
                background: "none", border: "none", outline: "none",
                color: C.textPri, fontSize: 12,
                fontFamily: "'JetBrains Mono', monospace",
                width: apiFocused ? 200 : 150,
                transition: "width 0.2s",
              }}
            />
          </div>

          <button style={{
            display: "flex", alignItems: "center", gap: 6,
            background: "transparent", border: `1px solid ${C.borderDef}`,
            borderRadius: 8, padding: "0 12px", height: 34, color: C.textSec,
            fontSize: 12, fontWeight: 500, cursor: "pointer",
          }}>
            <Icon name="account_circle" size={14} />
            Account
          </button>
        </div>
      </nav>

      {/* ─── CONTENT ─── */}
      <main style={{ paddingTop: 76, paddingBottom: 56, padding: "76px 24px 56px", maxWidth: 1180, margin: "0 auto" }}>

        {/* Page Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, letterSpacing: "-0.5px", color: C.textPri }}>Researcher Workbench</h1>
            <p style={{ margin: "5px 0 0", fontSize: 13, color: C.textTer }}>Format and generate academic documents with AI precision.</p>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <span style={{
              display: "inline-flex", alignItems: "center", gap: 6, padding: "4px 10px",
              background: C.successDim, border: "1px solid rgba(34,197,94,0.2)",
              borderRadius: 7, fontSize: 11, fontWeight: 600,
              color: C.success, fontFamily: "'JetBrains Mono', monospace",
            }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: C.success, boxShadow: `0 0 6px ${C.success}`, display: "inline-block" }} />
              READY
            </span>
            <span style={{
              display: "inline-flex", padding: "4px 10px",
              background: C.bgElevated, border: `1px solid ${C.borderSubtle}`,
              borderRadius: 7, fontSize: 11, color: C.textMuted,
              fontFamily: "'JetBrains Mono', monospace",
            }}>v2.1</span>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div style={{
            display: "flex", alignItems: "center", gap: 10,
            background: C.errorDim, border: "1px solid rgba(239,68,68,0.2)",
            borderRadius: 9, padding: "10px 14px",
            color: "#fca5a5", fontSize: 13, marginBottom: 16,
          }}>
            <Icon name="error" size={16} color="#ef4444" />
            {error}
          </div>
        )}

        {/* ─── MAIN CARD ─── */}
        <div style={{
          background: C.bgSurface,
          border: `1px solid ${C.borderSubtle}`,
          borderRadius: 16,
          overflow: "hidden",
          boxShadow: "0 0 0 1px rgba(255,255,255,0.03), 0 20px 60px rgba(0,0,0,0.5)",
        }}>

          {/* Tab bar */}
          <div style={{
            display: "flex", alignItems: "center",
            background: C.bgElevated,
            borderBottom: `1px solid ${C.borderFaint}`,
            padding: "0 8px",
            overflowX: "auto",
          }}>
            {tabs.map(t => {
              const active = activeTab === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  style={{
                    display: "flex", alignItems: "center", gap: 7,
                    padding: "12px 16px",
                    background: "none", border: "none",
                    borderBottom: `2px solid ${active ? C.accent : "transparent"}`,
                    color: active ? C.textPri : C.textMuted,
                    fontSize: 12.5, fontWeight: active ? 600 : 500,
                    cursor: "pointer", transition: "color 0.15s, border-color 0.15s",
                    whiteSpace: "nowrap", fontFamily: "'Inter', sans-serif",
                  }}
                >
                  <Icon name={t.icon} size={15} color={active ? C.accent : C.textMuted} />
                  {t.label}
                </button>
              );
            })}
          </div>

          {/* Content */}
          <div style={{ padding: 24 }}>

            {/* ── PASTE TEXT ── */}
            {activeTab === "text" && (
              <div 
                style={{ display: "flex", flexDirection: "column", gap: 16 }}
                onPaste={(e) => {
                  const items = e.clipboardData?.items;
                  if (!items) return;
                  const newImages: File[] = [];
                  for (let i = 0; i < items.length; i++) {
                    if (items[i].type.indexOf("image") !== -1) {
                      const file = items[i].getAsFile();
                      if (file) newImages.push(file);
                    }
                  }
                  if (newImages.length > 0) {
                    setImages(prev => [...prev, ...newImages]);
                  }
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <Label>Source Input</Label>
                    <span style={{ fontSize: 11, color: C.textMuted, fontFamily: "'JetBrains Mono', monospace" }}>
                      {text.length.toLocaleString()} chars
                    </span>
                  </div>
                  <TextAreaInput value={text} onChange={setText} placeholder={"// Paste your research notes, raw data,\n// or academic draft here for AI synthesis…"} />
                </div>
                
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                  <div>
                    <Label>Supporting Images (Upload or Paste)</Label>
                    <div style={{ 
                      border: `1px dashed ${C.borderDef}`, borderRadius: 8, padding: 12, 
                      display: "flex", flexDirection: "column", gap: 8, background: C.bgElevated
                    }}>
                      <input 
                        type="file" multiple accept="image/*" 
                        onChange={e => e.target.files && setImages(Array.from(e.target.files))} 
                        style={{ fontSize: 12, color: C.textSec }}
                      />
                      {images.length > 0 && (
                        <div style={{ fontSize: 11, color: C.accent }}>{images.length} images selected</div>
                      )}
                    </div>
                  </div>
                  <div>
                    <Label>Image Placement</Label>
                    <div style={{ display: "flex", gap: 6 }}>
                      {["Let AI Decide", "Top", "Bottom"].map(opt => (
                        <button
                          key={opt}
                          onClick={() => setImagePlacement(opt)}
                          style={{
                            flex: 1, padding: "8px 0",
                            background: imagePlacement === opt ? C.accentDim : "transparent",
                            border: `1px solid ${imagePlacement === opt ? C.accent : C.borderDef}`,
                            borderRadius: 6, color: imagePlacement === opt ? C.textPri : C.textSec,
                            fontSize: 11, fontWeight: imagePlacement === opt ? 600 : 500,
                            cursor: "pointer", transition: "all 0.15s"
                          }}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                <AdvancedLayout {...{
                  hFont,setHFont,hSize,setHSize,spacing,setSpacing,margin,setMargin,
                  cAlign,setCAlign,codeLang,setCodeLang,highlightCode,setHighlightCode,
                  autoNumbering,setAutoNumbering,continuousSections,setContinuousSections
                }} />
                <GenerateButton loading={loading} label="Generate Document" onClick={() => handleGenerate()} />
              </div>
            )}

            {/* ── UPLOAD ── */}
            {activeTab === "upload" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <Dropzone file={file} onFile={setFile} accept=".txt,.pdf,.docx" label="Drop your document (PDF, DOCX, TXT)" />
                <AdvancedLayout {...{
                  hFont,setHFont,hSize,setHSize,spacing,setSpacing,margin,setMargin,
                  cAlign,setCAlign,codeLang,setCodeLang,highlightCode,setHighlightCode,
                  autoNumbering,setAutoNumbering,continuousSections,setContinuousSections
                }} />
                <GenerateButton loading={loading} label="Format Document" onClick={() => handleGenerate()} />
              </div>
            )}

            {/* ── ACADEMIC REPORT ── */}
            {activeTab === "academic" && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 16, alignItems: "start" }}>

                {/* Left */}
                <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                  <SectionCard title="Repository & Project Data">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                      <div style={{ gridColumn: "span 2" }}>
                        <Label>Project Title</Label>
                        <Input value={projTitle} onChange={setProjTitle} placeholder="e.g., Federated Learning for Edge Computing" />
                      </div>
                      <div>
                        <Label>Source Code (ZIP)</Label>
                        <SmallDropzone file={projZip} onFile={setProjZip} accept=".zip" icon="folder_zip" label="Drop ZIP or browse…" />
                      </div>
                      <div>
                        <Label>GitHub Repository URL</Label>
                        <div style={{ position: "relative" }}>
                          <Icon name="link" size={14} color={C.textMuted} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", pointerEvents: "none" }} />
                          <Input value={githubUrl} onChange={setGithubUrl} placeholder="https://github.com/…" mono style={{ paddingLeft: 30 }} />
                        </div>
                      </div>
                      <div>
                        <Label>University / Institution</Label>
                        <Input value={university} onChange={setUniversity} placeholder="e.g., Anna University" />
                      </div>
                      <div>
                        <Label>Degree / Programme</Label>
                        <Input value={degree} onChange={setDegree} placeholder="e.g., B.Tech Computer Science" />
                      </div>
                      <div>
                        <Label>Department</Label>
                        <Input value={dept} onChange={setDept} placeholder="e.g., Dept. of CSE" />
                      </div>
                      <div>
                        <Label>Academic Year</Label>
                        <Input value={acYear} onChange={setAcYear} placeholder="e.g., 2024–2025" />
                      </div>
                      <div>
                        <Label>Project Guide / Supervisor</Label>
                        <Input value={guide} onChange={setGuide} placeholder="Dr. John Doe" />
                      </div>
                      <div>
                        <Label>Guide Designation</Label>
                        <Input value={guideDesig} onChange={setGuideDesig} placeholder="Assistant Professor" />
                      </div>
                      <div>
                        <Label>Head of Department (HOD)</Label>
                        <Input value={hod} onChange={setHod} placeholder="Prof. Jane Smith" />
                      </div>
                      <div>
                        <Label>HOD Designation</Label>
                        <Input value={hodDesig} onChange={setHodDesig} placeholder="Professor & Head" />
                      </div>
                      <div style={{ gridColumn: "1 / -1" }}>
                        <Label>Principal</Label>
                        <Input value={principal} onChange={setPrincipal} placeholder="Dr. Alan Turing" />
                      </div>
                    </div>
                  </SectionCard>

                  <SectionCard
                    title="Team Members"
                    right={
                      <button
                        onClick={() => setTeamMembers(m => [...m, ""])}
                        style={{
                          display: "flex", alignItems: "center", gap: 5,
                          background: "transparent", border: `1px solid ${C.borderDef}`,
                          borderRadius: 7, padding: "4px 10px",
                          color: C.textSec, fontSize: 11.5, fontWeight: 500, cursor: "pointer",
                        }}
                      >
                        <Icon name="add" size={13} color={C.textSec} />
                        Add Member
                      </button>
                    }
                  >
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                      {teamMembers.map((name, i) => (
                        <MemberRow
                          key={i}
                          value={name}
                          index={i}
                          onChange={v => setTeamMembers(m => m.map((x, j) => j === i ? v : x))}
                          onRemove={() => setTeamMembers(m => m.filter((_, j) => j !== i))}
                          canRemove={teamMembers.length > 1}
                        />
                      ))}
                    </div>
                  </SectionCard>
                </div>

                {/* Right */}
                <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                  <SectionCard title="Generate">
                    <GenerateButton loading={loading} label="Generate Academic Report" onClick={() => handleGenerate()} />
                    <p style={{ marginTop: 10, fontSize: 11, color: C.textMuted, textAlign: "center", lineHeight: 1.6 }}>
                      Est. 2–4 min. The AI auto-generates chapters,<br />UML diagrams, and code analysis.
                    </p>
                  </SectionCard>

                  <SectionCard title="Output Includes">
                    {[
                      ["description", "Abstract & Introduction"],
                      ["account_tree", "System Architecture"],
                      ["code", "Code Analysis (Ch. 4)"],
                      ["bar_chart", "Test Results & Metrics"],
                      ["format_quote", "References & Citations"],
                    ].map(([icon, label]) => (
                      <div key={label} style={{
                        display: "flex", alignItems: "center", gap: 10,
                        padding: "8px 0", borderBottom: `1px solid ${C.borderFaint}`,
                        fontSize: 12.5, color: C.textSec,
                      }}>
                        <Icon name={icon} size={14} color={C.accent} />
                        {label}
                      </div>
                    ))}
                  </SectionCard>
                </div>
              </div>
            )}

          </div>
        </div>

        {/* Footer */}
        <p style={{ textAlign: "center", marginTop: 32, fontSize: 11, color: C.textMuted, fontFamily: "'JetBrains Mono', monospace" }}>
          © 2026 WriteX Academic Engine · BYOK · $0 Infrastructure
        </p>
      </main>

      {/* ─── CONFLICT MODAL ─── */}
      {showConflict && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)",
          backdropFilter: "blur(10px)", zIndex: 100,
          display: "flex", alignItems: "center", justifyContent: "center", padding: 20,
        }}>
          <div style={{
            background: C.bgSurface, border: `1px solid ${C.borderDef}`,
            borderRadius: 18, padding: 28, maxWidth: 580, width: "100%",
            maxHeight: "85vh", overflowY: "auto",
            boxShadow: `0 25px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(99,102,241,0.15)`,
          }}>
            <div style={{ display: "flex", gap: 14, marginBottom: 20 }}>
              <div style={{
                width: 38, height: 38, borderRadius: 10, flexShrink: 0,
                background: "rgba(245,158,11,0.1)", border: "1px solid rgba(245,158,11,0.25)",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <Icon name="warning" size={18} color={C.warn} />
              </div>
              <div>
                <h2 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: C.textPri }}>Style Conflict Detected</h2>
                <p style={{ margin: "4px 0 0", fontSize: 13, color: C.textSec }}>
                  Your special requests conflict with the reference file. Choose which to apply for each.
                </p>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {conflicts.map((c) => {
                const res = resolved[c.parameter_key];
                return (
                  <div key={c.parameter_key} style={{
                    background: res ? "rgba(99,102,241,0.06)" : C.bgElevated,
                    border: `1px solid ${res ? "rgba(99,102,241,0.2)" : C.borderSubtle}`,
                    borderRadius: 10, padding: 14,
                  }}>
                    <Label>{c.parameter_label}</Label>
                    {res === undefined ? (
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                        {[["Reference File", c.reference_value, false], ["Special Request", c.request_value, true]].map(([lab, val, isDanger]) => (
                          <button
                            key={String(lab)}
                            onClick={() => setResolved(prev => ({ ...prev, [c.parameter_key]: String(val) }))}
                            style={{
                              background: isDanger ? "rgba(239,68,68,0.06)" : C.bgOverlay,
                              border: `1px solid ${isDanger ? "rgba(239,68,68,0.2)" : C.borderDef}`,
                              borderRadius: 9, padding: "10px 12px",
                              cursor: "pointer", textAlign: "left", transition: "border-color 0.15s",
                            }}
                          >
                            <span style={{ fontSize: 10, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.08em", display: "block", marginBottom: 5, fontFamily: "'JetBrains Mono', monospace" }}>{String(lab)}</span>
                            <span style={{ fontSize: 13, color: C.textPri, fontWeight: 500 }}>{String(val)}</span>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div style={{
                        display: "flex", alignItems: "center", justifyContent: "space-between",
                        background: C.accentDim, borderRadius: 8, padding: "8px 12px",
                      }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <Icon name="check_circle" size={15} color={C.accent} />
                          <span style={{ fontSize: 13, color: C.textPri, fontWeight: 500 }}>{res}</span>
                        </div>
                        <button
                          onClick={() => setResolved(prev => { const n = {...prev}; delete n[c.parameter_key]; return n; })}
                          style={{ background: "none", border: "none", cursor: "pointer", fontSize: 11, color: C.textMuted, textDecoration: "underline" }}
                        >Undo</button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <div style={{ display: "flex", gap: 10, marginTop: 20, paddingTop: 16, borderTop: `1px solid ${C.borderFaint}` }}>
              <button
                onClick={() => { setShowConflict(false); setResolved({}); setConflicts([]); }}
                style={{
                  flex: 1, height: 38, background: "transparent",
                  border: `1px solid ${C.borderDef}`, borderRadius: 9,
                  color: C.textSec, fontSize: 13, fontWeight: 500, cursor: "pointer",
                }}
              >Cancel</button>
              <button
                disabled={Object.keys(resolved).length !== conflicts.length || loading}
                onClick={() => handleGenerate(true)}
                style={{
                  flex: 2, height: 38, background: C.accent,
                  border: "none", borderRadius: 9, color: "white",
                  fontSize: 13, fontWeight: 600, cursor: "pointer",
                  opacity: Object.keys(resolved).length !== conflicts.length ? 0.5 : 1,
                  display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                }}
              >
                <Icon name="done_all" size={15} color="white" />
                Confirm &amp; Generate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function TextAreaInput({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder: string }) {
  const [focused, setFocused] = useState(false);
  return (
    <textarea
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      style={{
        width: "100%", minHeight: 260, resize: "vertical",
        background: C.bgOverlay, border: `1px solid ${focused ? C.accent : C.borderDef}`,
        borderRadius: 10, padding: 16,
        fontFamily: "'JetBrains Mono', monospace", fontSize: 12.5, lineHeight: 1.75,
        color: C.textPri, outline: "none",
        boxShadow: focused ? `0 0 0 3px ${C.accentDim}` : "none",
        transition: "border-color 0.15s, box-shadow 0.15s",
        boxSizing: "border-box", display: "block",
      }}
    />
  );
}

function Dropzone({ file, onFile, accept, label }: { file: File|null; onFile: (f: File|null) => void; accept: string; label: string }) {
  const [hov, setHov] = useState(false);
  return (
    <div
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        position: "relative", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        gap: 14, minHeight: 220, border: `1.5px dashed ${hov ? C.accent : C.borderDef}`,
        borderRadius: 12, background: hov ? C.accentDim : C.bgElevated,
        cursor: "pointer", transition: "border-color 0.2s, background 0.2s",
      }}
    >
      <input type="file" accept={accept} onChange={e => onFile(e.target.files?.[0] ?? null)} style={{ position: "absolute", inset: 0, opacity: 0, cursor: "pointer" }} />
      <div style={{ width: 52, height: 52, borderRadius: 13, background: C.bgOverlay, border: `1px solid ${C.borderDef}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Icon name="upload_file" size={24} color={C.accent} />
      </div>
      {file ? (
        <div style={{ textAlign: "center" }}>
          <p style={{ margin: 0, fontWeight: 600, color: C.textPri, fontSize: 13 }}>{file.name}</p>
          <p style={{ margin: "3px 0 0", fontSize: 12, color: C.textTer }}>{(file.size/1024).toFixed(1)} KB · click to replace</p>
        </div>
      ) : (
        <div style={{ textAlign: "center" }}>
          <p style={{ margin: 0, fontWeight: 600, color: C.textPri, fontSize: 13 }}>{label}</p>
          <p style={{ margin: "3px 0 0", fontSize: 12, color: C.textTer }}>Click or drag & drop to browse</p>
        </div>
      )}
    </div>
  );
}

function SmallDropzone({ file, onFile, accept, icon, label }: { file: File|null; onFile: (f: File|null) => void; accept: string; icon: string; label: string }) {
  const [hov, setHov] = useState(false);
  return (
    <div
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        position: "relative", display: "flex", alignItems: "center", gap: 8,
        height: 40, padding: "0 12px", border: `1px dashed ${hov ? C.accent : C.borderDef}`,
        borderRadius: 8, background: hov ? C.accentDim : C.bgOverlay, cursor: "pointer",
        transition: "border-color 0.15s, background 0.15s", overflow: "hidden",
      }}
    >
      <input type="file" accept={accept} onChange={e => onFile(e.target.files?.[0] ?? null)} style={{ position: "absolute", inset: 0, opacity: 0, cursor: "pointer" }} />
      <Icon name={icon} size={15} color={C.textMuted} />
      {file
        ? <span style={{ fontSize: 12, color: C.accent, fontFamily: "'JetBrains Mono', monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{file.name}</span>
        : <span style={{ fontSize: 12.5, color: C.textSec }}>{label}</span>
      }
    </div>
  );
}

function MemberRow({ value, index, onChange, onRemove, canRemove }: { value: string; index: number; onChange: (v: string) => void; onRemove: () => void; canRemove: boolean }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8,
      background: C.bgOverlay, border: `1px solid ${focused ? C.accent : C.borderSubtle}`,
      borderRadius: 8, padding: "6px 10px",
      transition: "border-color 0.15s",
    }}>
      <Icon name="drag_indicator" size={14} color={C.textMuted} />
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder={`Member ${index + 1}…`}
        style={{ flex: 1, background: "none", border: "none", outline: "none", fontSize: 13, color: C.textPri, fontFamily: "'Inter', sans-serif" }}
      />
      {canRemove && (
        <button onClick={onRemove} style={{ background: "none", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", width: 22, height: 22, borderRadius: 5, color: C.textMuted, padding: 0 }}>
          <Icon name="close" size={13} />
        </button>
      )}
    </div>
  );
}

function GenerateButton({ loading, label, onClick }: { loading: boolean; label: string; onClick: () => void }) {
  const [hov, setHov] = useState(false);
  return (
    <button
      disabled={loading}
      onClick={onClick}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 9,
        padding: "11px 20px", border: "none", borderRadius: 10,
        background: loading ? C.bgSubtle : hov ? C.accentHov : C.accent,
        color: "white", fontSize: 13.5, fontWeight: 600, cursor: loading ? "not-allowed" : "pointer",
        boxShadow: !loading && hov ? `0 0 28px ${C.accentGlow}` : "none",
        transition: "background 0.15s, box-shadow 0.15s, transform 0.1s",
        transform: hov && !loading ? "translateY(-1px)" : "none",
        opacity: loading ? 0.6 : 1,
        fontFamily: "'Inter', sans-serif",
      }}
    >
      <Icon name="auto_awesome" size={16} color="white" style={{ fontVariationSettings: "'FILL' 1" }} />
      {loading ? "Processing…" : label}
    </button>
  );
}

const AdvancedLayout = ({
  hFont, setHFont, hSize, setHSize, spacing, setSpacing, margin, setMargin,
  cAlign, setCAlign, codeLang, setCodeLang, highlightCode, setHighlightCode,
  autoNumbering, setAutoNumbering, continuousSections, setContinuousSections
}: any) => {
  return (
    <div style={{ background: C.bgElevated, border: `1px solid ${C.borderSubtle}`, borderRadius: 10, overflow: "hidden" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 7, padding: "9px 14px", borderBottom: `1px solid ${C.borderFaint}`, background: "rgba(255,255,255,0.015)" }}>
        <Icon name="tune" size={14} color={C.textMuted} />
        <span style={{ fontSize: 10.5, fontWeight: 600, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.09em", fontFamily: "'JetBrains Mono', monospace" }}>Advanced Layout Settings</span>
      </div>
      <div style={{ padding: 14, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
        <div><Label>Heading Font</Label>
          <Select value={hFont} onChange={setHFont} options={["Times New Roman","Arial","Calibri","Helvetica","Georgia"]} />
        </div>
        <div><Label>Font Size (pt)</Label>
          <Input value={hSize} onChange={setHSize} type="number" mono />
        </div>
        <div><Label>Line Spacing</Label>
          <Input value={spacing} onChange={setSpacing} type="number" mono />
        </div>
        <div><Label>Margin (mm)</Label>
          <Input value={margin} onChange={setMargin} type="number" mono />
        </div>
        <div>
          <Label>Alignment</Label>
          <div style={{ display: "flex", background: C.bgOverlay, border: `1px solid ${C.borderDef}`, borderRadius: 8, overflow: "hidden", height: 36 }}>
            {[["Left","format_align_left"],["Center","format_align_center"],["Justify","format_align_justify"]].map(([a, icon]) => (
              <button key={a} onClick={() => setCAlign(a)} style={{
                flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
                background: cAlign === a ? C.accentDim : "transparent",
                border: "none", borderRight: a !== "Justify" ? `1px solid ${C.borderSubtle}` : "none",
                cursor: "pointer", transition: "background 0.15s",
                color: cAlign === a ? C.accent : C.textMuted,
              }}>
                <Icon name={icon} size={14} color={cAlign === a ? C.accent : C.textMuted} />
              </button>
            ))}
          </div>
        </div>
        <div><Label>Code Style</Label>
          <Select value={codeLang} onChange={setCodeLang} options={["Auto","Python","JavaScript","Java","C++","Go","R","None"]} />
        </div>
        {autoNumbering !== undefined && (
          <div>
            <Label>Auto Numbering</Label>
            <div style={{ display: "flex", gap: 4 }}>
              <button onClick={() => setAutoNumbering(true)} style={{
                flex: 1, height: 36, background: autoNumbering ? C.accentDim : "transparent",
                border: `1px solid ${autoNumbering ? C.accent : C.borderDef}`,
                borderRadius: 8, color: autoNumbering ? C.textPri : C.textSec, cursor: "pointer", fontSize: 12, fontWeight: 500
              }}>On</button>
              <button onClick={() => setAutoNumbering(false)} style={{
                flex: 1, height: 36, background: !autoNumbering ? C.accentDim : "transparent",
                border: `1px solid ${!autoNumbering ? C.accent : C.borderDef}`,
                borderRadius: 8, color: !autoNumbering ? C.textPri : C.textSec, cursor: "pointer", fontSize: 12, fontWeight: 500
              }}>Off</button>
            </div>
          </div>
        )}
        {continuousSections !== undefined && (
          <div>
            <Label>Page Breaks</Label>
            <div style={{ display: "flex", gap: 4 }}>
              <button onClick={() => setContinuousSections(false)} style={{
                flex: 1, height: 36, background: !continuousSections ? C.accentDim : "transparent",
                border: `1px solid ${!continuousSections ? C.accent : C.borderDef}`,
                borderRadius: 8, color: !continuousSections ? C.textPri : C.textSec, cursor: "pointer", fontSize: 12, fontWeight: 500
              }}>Strict</button>
              <button onClick={() => setContinuousSections(true)} style={{
                flex: 1, height: 36, background: continuousSections ? C.accentDim : "transparent",
                border: `1px solid ${continuousSections ? C.accent : C.borderDef}`,
                borderRadius: 8, color: continuousSections ? C.textPri : C.textSec, cursor: "pointer", fontSize: 12, fontWeight: 500
              }}>Continuous</button>
            </div>
          </div>
        )}
        {highlightCode !== undefined && (
          <div>
            <Label>Highlight Code</Label>
            <div style={{ display: "flex", gap: 4 }}>
              <button onClick={() => setHighlightCode(true)} style={{
                flex: 1, height: 36, background: highlightCode ? C.accentDim : "transparent",
                border: `1px solid ${highlightCode ? C.accent : C.borderDef}`,
                borderRadius: 8, color: highlightCode ? C.textPri : C.textSec, cursor: "pointer", fontSize: 12, fontWeight: 500
              }}>On</button>
              <button onClick={() => setHighlightCode(false)} style={{
                flex: 1, height: 36, background: !highlightCode ? C.accentDim : "transparent",
                border: `1px solid ${!highlightCode ? C.accent : C.borderDef}`,
                borderRadius: 8, color: !highlightCode ? C.textPri : C.textSec, cursor: "pointer", fontSize: 12, fontWeight: 500
              }}>Off</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
