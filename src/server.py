from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import io
import json
import re

from src.ai.structurer import structure_text
from src.file_formatting.formatting import generate_report, StyleConfig
from docx.enum.text import WD_ALIGN_PARAGRAPH
from src.api_academic import router as academic_router

app = FastAPI(title="WriteX API", description="Academic Report Generation API")

app.include_router(academic_router)

# Setup CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the vercel domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_style_config(style_json_str: str) -> StyleConfig:
    try:
        if not style_json_str:
            return StyleConfig()  # Use defaults
            
        cfg_dict = json.loads(style_json_str)
        align_map = {
            "Left": WD_ALIGN_PARAGRAPH.LEFT, 
            "Center": WD_ALIGN_PARAGRAPH.CENTER, 
            "Right": WD_ALIGN_PARAGRAPH.RIGHT, 
            "Justify": WD_ALIGN_PARAGRAPH.JUSTIFY
        }
        
        return StyleConfig(
            margin_inches=cfg_dict.get("margin_inches", 1.0),
            heading_font=cfg_dict.get("heading_font", "Times New Roman"),
            heading_size_pt=cfg_dict.get("heading_size_pt", 14.0),
            heading_bold=cfg_dict.get("heading_bold", True),
            chapter_alignment=align_map.get(cfg_dict.get("chapter_alignment", "Center"), WD_ALIGN_PARAGRAPH.CENTER),
            subheading_alignment=align_map.get(cfg_dict.get("subheading_alignment", "Left"), WD_ALIGN_PARAGRAPH.LEFT),
            content_font=cfg_dict.get("content_font", "Times New Roman"),
            content_size_pt=cfg_dict.get("content_size_pt", 12.0),
            content_alignment=align_map.get(cfg_dict.get("content_alignment", "Justify"), WD_ALIGN_PARAGRAPH.JUSTIFY),
            line_spacing=cfg_dict.get("line_spacing", 1.5),
            space_before_pt=cfg_dict.get("space_before_pt", 0.0),
            space_after_pt=cfg_dict.get("space_after_pt", 0.0),
            code_language=cfg_dict.get("code_language", "Auto"),
            continuous_sections=cfg_dict.get("continuous_sections", False),
            auto_numbering=cfg_dict.get("auto_numbering", True)
        )
    except Exception as e:
        print(f"Error parsing style config: {e}")
        return StyleConfig()

def process_formatting(
    text_content: str,
    api_key: str,
    style_name: str,
    style_cfg: StyleConfig,
    images: List[UploadFile],
    image_placement: str,
    provider: str = "groq",
    model_name: Optional[str] = None,
):
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key is required")
        
    try:
        image_names = [img.filename for img in images] if images else []
        struct = structure_text(
            text_content,
            api_key=api_key,
            style_name=style_name,
            available_images=image_names,
            provider=provider,
            model_name=model_name,
        )
        
        # Extract JSON array from response
        json_match = re.search(r"\[.*\]", struct, re.DOTALL)
        data = json.loads(json_match.group(0)) if json_match else []

        if images:
            img_nodes = []
            for img in images:
                file_bytes = img.file.read()
                img_nodes.append({"type": "image", "content": file_bytes, "filename": img.filename})
                
            if image_placement == "Top":
                data = img_nodes + data
            elif image_placement == "Bottom":
                data = data + img_nodes
            else:
                # Let AI Decide logic
                new_data = []
                for block in data:
                    if block.get("type") == "image_insertion":
                        fname = block.get("filename")
                        matched = next((node for node in img_nodes if node["filename"] == fname), None)
                        if matched:
                            new_data.append(matched)
                    else:
                        new_data.append(block)
                
                # Append leftover images
                used_fnames = [b.get("filename") for b in new_data if b.get("type") == "image"]
                for node in img_nodes:
                    if node["filename"] not in used_fnames:
                        new_data.append(node)
                        
                data = new_data

        buf = io.BytesIO()
        generate_report(data, buf, style_name=style_name, style_config=style_cfg)
        buf.seek(0)
        return buf
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/format_text")
def api_format_text(
    text: str = Form(...),
    api_key: str = Form(...),
    style_name: str = Form("Academic"),
    style_config: str = Form("{}"),
    image_placement: str = Form("Let AI Decide"),
    provider: str = Form("groq"),
    model_name: Optional[str] = Form(None),
    images: List[UploadFile] = File(None),
):
    style_cfg = parse_style_config(style_config)
    buf = process_formatting(text, api_key, style_name, style_cfg, images or [], image_placement, provider, model_name)
    
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=formatted.docx"}
    )

@app.post("/api/format_file")
def api_format_file(
    file: UploadFile = File(...),
    api_key: str = Form(...),
    style_name: str = Form("Academic"),
    style_config: str = Form("{}"),
    image_placement: str = Form("Let AI Decide"),
    provider: str = Form("groq"),
    model_name: Optional[str] = Form(None),
    images: List[UploadFile] = File(None),
):
    try:
        file_bytes = file.file.read()
        
        if file.filename.endswith('.txt'):
            file_txt = file_bytes.decode('utf-8')
        elif file.filename.endswith('.pdf'):
            import pypdf
            pdf_io = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(pdf_io)
            # Fix: use real newline \n, not escaped literal \\n
            file_txt = "\n".join([p.extract_text() or "" for p in reader.pages])
        elif file.filename.endswith('.docx'):
            from docx import Document
            docx_io = io.BytesIO(file_bytes)
            doc = Document(docx_io)
            # Fix: use real newline \n, not escaped literal \\n
            file_txt = "\n".join([p.text for p in doc.paragraphs])
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use PDF, DOCX, or TXT.")
            
        style_cfg = parse_style_config(style_config)
        buf = process_formatting(file_txt, api_key, style_name, style_cfg, images or [], image_placement, provider, model_name)
        
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=formatted_file.docx"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=True)
