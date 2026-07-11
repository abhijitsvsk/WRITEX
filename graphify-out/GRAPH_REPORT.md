# Graph Report - .  (2026-04-30)

## Corpus Check
- 104 files · ~94,920 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 377 nodes · 680 edges · 41 communities detected
- Extraction: 55% EXTRACTED · 45% INFERRED · 0% AMBIGUOUS · INFERRED: 308 edges (avg confidence: 0.65)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]

## God Nodes (most connected - your core abstractions)
1. `ReportGenerator` - 45 edges
2. `Blueprint` - 23 edges
3. `ProjectSummary` - 22 edges
4. `CodeAnalyzer` - 21 edges
5. `DocumentValidator` - 21 edges
6. `Architect` - 20 edges
7. `DocumentNode` - 20 edges
8. `AntResult` - 19 edges
9. `generate_report()` - 19 edges
10. `ContentAnt` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Returns JSON-safe dict. detailed_analysis is NOT included here         because` --uses--> `CodeAnalysisResult`  [INFERRED]
  src\analysis\project_summary.py → src\analysis\code_parser.py
- `Represents a node in the document structure.` --uses--> `ProjectSummary`  [INFERRED]
  src\blast\blueprint.py → src\analysis\project_summary.py
- `Update a node's state.` --uses--> `ProjectSummary`  [INFERRED]
  src\blast\blueprint.py → src\analysis\project_summary.py
- `Return global context.` --uses--> `ProjectSummary`  [INFERRED]
  src\blast\blueprint.py → src\analysis\project_summary.py
- `main()` --calls--> `generate_report()`  [INFERRED]
  cli_report_gen.py → src\file_formatting\formatting.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (34): main(), DocumentCompiler, Builds a human-readable constraint block that is prepended to every LLM system p, Validates the generated AST blocks to prevent silent document corruption before, Parses JSON blocks returned by the LLM and formats them into the AST structure., Deterministically generates references from the analyzed tech stack to avoid LLM, The Core Orchestrator.     Strictly separates UI states from structure executio, Executes the content generation phase. Returns the pre-validation structure arra (+26 more)

### Community 1 - "Community 1"
Cohesion: 0.1
Nodes (32): ABC, Ant, Architect, The Architect orchestrates the execution flow.     It selects the right Ant for, Execute the appropriate Ant with retry logic., Compiles the blueprint into a final document., Analyze the blueprint and determine next steps., Factory method to get the right Ant. (+24 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (22): CodeAnalyzer, Extracts and analyzes a ZIP file (from a file-like object or path) in-memory., ClassInfo, CodeAnalysisResult, CodeParser, FunctionInfo, merge_analysis_results(), AST-based code parser for extracting real code structure. Part of Phase 2: Real (+14 more)

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (26): add_list_of_figures(), _add_page_numbers(), add_table_of_contents(), generate_report(), _patch_toc_lof_pages(), _postbuild_estimate_pages(), POST-BUILD page estimator.  Walks ALL body elements (paragraphs and tables), Walk the built Document and replace every '?' placeholder in TOC/LOF     entrie (+18 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (16): MockStyleAnalyzer, main(), main(), await_module_availability(), Extracts specific sections verbatim from the sample report.         Target sect, Analyzes sample reports to extract style and formatting guidelines., Generates a style guide string based on the text.         (In a real scenario,, Analyzes the text to detect structural conventions (e.g., numbered headings). (+8 more)

### Community 5 - "Community 5"
Cohesion: 0.11
Nodes (15): Blueprint, The Blueprint maintains the state of the project and the document.     It is th, Load initial structure from list of dicts., Return list of nodes that need processing., Set a global context value., Serialize state for persistence., Persist state to disk., Load state from disk. (+7 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (15): MockSummary, Comprehensive structural validation test for the academic report pipeline. Test, Validator should pass a well-formed structure., Validator should remove placeholder reference text., Validator should inject LOF before TOC if figures exist but LOF is missing., test_validator_clean_structure(), test_validator_heals_missing_lof(), test_validator_heals_reference_placeholder() (+7 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (19): check_single_conflict(), detect_conflicts(), normalise_reference_params(), Conflict detection engine for Special Requests vs Reference Document parameters., Checks whether a single new value conflicts with the cached reference params., Converts StyleAnalyzer output keys into SpecialRequest-compatible keys     using, Compares a SpecialRequest's parameters against the extracted reference parameter, ConflictRecord (+11 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (6): run_formatting(), format_detailed_analysis_for_prompt(), Helper to format code analysis results for LLM prompts., Format CodeAnalysisResult into a string for LLM prompt injection.     This repl, structure_text(), test_ai_connection()

### Community 9 - "Community 9"
Cohesion: 0.24
Nodes (11): _build_page_map_com(), _normalize(), _patch_docx(), patch_toc_with_real_pages(), toc_patcher.py — Permanent Native MS Word TOC/LOF page number resolver.  ARCHI, Two-pass TOC/LOF page number resolution using Native Windows MS Word., Collapse whitespace and lowercase for fuzzy comparison., Read back the TOC/LOF entries that were written with '?' placeholders.     Retu (+3 more)

### Community 10 - "Community 10"
Cohesion: 0.29
Nodes (6): build_mermaid_diagram(), extract_file_structure(), generate_basic_summary(), Optional pipeline stub: Generates a lightweight natural language summary      of, Safely parses Python abstract syntax trees to extract structural metadata     wi, Constructs a valid Mermaid.js dependency graph (`graph TD`) mapped strictly

### Community 11 - "Community 11"
Cohesion: 0.5
Nodes (3): Post-processing module that uses Microsoft Word to force-update all fields  (TO, Opens the generated .docx in Microsoft Word via a VBScript subprocess,     forc, update_toc_via_com()

### Community 12 - "Community 12"
Cohesion: 0.67
Nodes (2): extract_json(), Extracts the JSON array from AI output.     This handles cases where Gemini add

### Community 13 - "Community 13"
Cohesion: 0.67
Nodes (2): mock_groq_api(), Globally intercepts Groq API calls across all tests unless explicitly bypassed.

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (0): 

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (0): 

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (0): 

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (0): 

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (0): 

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (0): 

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (0): 

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (0): 

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (0): 

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (0): 

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (0): 

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (0): 

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Execute the Ant's task.         :param payload: The specific data to work on (e

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (0): 

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (0): 

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (1): Sanitizes a single string.

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): Recursively sanitizes dictionaries and lists (e.g., AST Project Summary).

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (0): 

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (0): 

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (0): 

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (0): 

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (0): 

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (0): 

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (0): 

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (0): 

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **61 isolated node(s):** `Safely parses Python abstract syntax trees to extract structural metadata     wi`, `Optional pipeline stub: Generates a lightweight natural language summary      of`, `Constructs a valid Mermaid.js dependency graph (`graph TD`) mapped strictly`, `Extracts the JSON array from AI output.     This handles cases where Gemini add`, `Helper to format code analysis results for LLM prompts.` (+56 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 14`** (2 nodes): `extract_specific_sections_debug()`, `debug_ack_extraction.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (2 nodes): `verify_app_startup.py`, `verify_startup()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `com_update.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `debug_sdt.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `e2e_test.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `run_demo.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `test_ack_template.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `test_model.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `Execute the Ant's task.         :param payload: The specific data to work on (e`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `Sanitizes a single string.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `Recursively sanitizes dictionaries and lists (e.g., AST Project Summary).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `check_schema.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `text_strt_1.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `verify_app_startup.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `verify_code_analysis.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `verify_report_generator.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `debug_structurer.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `verify_app_imports.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `verify_imports.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ReportGenerator` connect `Community 0` to `Community 1`, `Community 2`, `Community 4`, `Community 6`, `Community 8`?**
  _High betweenness centrality (0.298) - this node is a cross-community bridge._
- **Why does `generate_report()` connect `Community 3` to `Community 0`, `Community 8`, `Community 4`, `Community 5`?**
  _High betweenness centrality (0.171) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 4` to `Community 0`, `Community 2`, `Community 3`, `Community 5`?**
  _High betweenness centrality (0.168) - this node is a cross-community bridge._
- **Are the 31 inferred relationships involving `ReportGenerator` (e.g. with `DataSanitizer` and `ContentAnt`) actually correct?**
  _`ReportGenerator` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `Blueprint` (e.g. with `Architect` and `The Architect orchestrates the execution flow.     It selects the right Ant for`) actually correct?**
  _`Blueprint` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `ProjectSummary` (e.g. with `CodeAnalyzer` and `Extracts and analyzes a ZIP file (from a file-like object or path) in-memory.`) actually correct?**
  _`ProjectSummary` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `CodeAnalyzer` (e.g. with `ProjectSummary` and `CodeParser`) actually correct?**
  _`CodeAnalyzer` has 9 INFERRED edges - model-reasoned connections that need verification._