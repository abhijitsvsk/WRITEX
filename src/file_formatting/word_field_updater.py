"""
Post-processing module that uses Microsoft Word to force-update all fields 
(TOC, LOF, page numbers) after document generation.

Uses a VBScript approach via subprocess to avoid COM initialization hangs
and dialog prompts that occur with direct win32com usage.
"""
import os
import sys
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)

_VBS_TEMPLATE = '''
On Error Resume Next

Dim objWord
Set objWord = CreateObject("Word.Application")
objWord.Visible = False
objWord.DisplayAlerts = 0

Dim objDoc
Set objDoc = objWord.Documents.Open("{docx_path}", False, False)

If Err.Number <> 0 Then
    WScript.Echo "ERROR_OPEN:" & Err.Description
    objWord.Quit
    WScript.Quit 1
End If

' Update all fields in the document body
objDoc.Content.Fields.Update

' Update each Table of Contents
Dim toc
For Each toc In objDoc.TablesOfContents
    toc.Update
Next

' Update each Table of Figures  
Dim tof
For Each tof In objDoc.TablesOfFigures
    tof.Update
Next

' Update fields in headers and footers
Dim sec
For Each sec In objDoc.Sections
    sec.Headers(1).Range.Fields.Update
    sec.Footers(1).Range.Fields.Update
Next

objDoc.Save
objDoc.Close False
objWord.Quit

If Err.Number <> 0 Then
    WScript.Echo "ERROR:" & Err.Description
    WScript.Quit 1
Else
    WScript.Echo "SUCCESS"
    WScript.Quit 0
End If
'''


def update_toc_via_com(docx_path: str) -> bool:
    """
    Opens the generated .docx in Microsoft Word via a VBScript subprocess,
    forces all fields (TOC, LOF, page numbers) to update,
    then saves and closes the document.

    Args:
        docx_path: Absolute or relative path to the .docx file.

    Returns:
        True if successful, False if Word is not available or update failed.
    """
    if sys.platform != "win32":
        logger.warning("[TOC-UPDATE] VBS automation only available on Windows. Skipping.")
        return False

    abs_path = os.path.abspath(docx_path).replace("\\", "\\\\")
    if not os.path.exists(os.path.abspath(docx_path)):
        logger.error(f"[TOC-UPDATE] File not found: {abs_path}")
        return False

    # Generate the VBS script with the document path injected
    vbs_content = _VBS_TEMPLATE.replace("{docx_path}", abs_path)

    # Write VBS to a temporary file
    vbs_fd, vbs_path = tempfile.mkstemp(suffix=".vbs")
    try:
        with os.fdopen(vbs_fd, "w") as f:
            f.write(vbs_content)

        # Execute the VBS script via cscript (headless Windows Script Host)
        result = subprocess.run(
            ["cscript", "//NoLogo", vbs_path],
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout  
        )

        output = result.stdout.strip()
        if "SUCCESS" in output:
            logger.info(f"[TOC-UPDATE] Successfully updated all fields via VBS in: {docx_path}")
            return True
        else:
            error_msg = output or result.stderr.strip()
            logger.warning(f"[TOC-UPDATE] VBS update returned: {error_msg}")
            return False

    except subprocess.TimeoutExpired:
        logger.warning("[TOC-UPDATE] VBS script timed out after 60 seconds.")
        return False
    except FileNotFoundError:
        logger.warning("[TOC-UPDATE] cscript not found. Windows Script Host may be disabled.")
        return False
    except Exception as e:
        logger.error(f"[TOC-UPDATE] VBS automation failed: {e}")
        return False
    finally:
        try:
            os.unlink(vbs_path)
        except Exception:
            pass
