import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.compiler import REPORT_SCHEMA

print(f"Total chapters: {len(REPORT_SCHEMA)}")
for i, c in enumerate(REPORT_SCHEMA):
    title = c["title"]
    subs = c["subsections"]
    print(f"\nChapter {i+1}: {title}")
    for s in subs:
        if isinstance(s, dict):
            sub_title = s["title"]
            subsubs = s.get("subsubsections", [])
            print(f"  > {sub_title} ({len(subsubs)} sub-subsections)")
            for ss in subsubs:
                print(f"      > {ss}")
        else:
            print(f"  > {s}")
