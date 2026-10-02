#!/usr/bin/env python3
"""
Convert academic documents (PDF, DOCX, PPTX, XLSX, HTML, TXT) into Markdown
using Microsoft's MarkItDown library.
"""
import argparse
import json
import sys
from pathlib import Path
from markitdown import MarkItDown

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def convert_document(input_path: Path) -> dict:
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")
    
    md = MarkItDown()
    result = md.convert(str(input_path))
    content = (result.text_content or "").strip()
    
    # Infer title from first H1 header or file stem
    title = input_path.stem
    for line in content.splitlines():
        line_clean = line.strip()
        if line_clean.startswith("# "):
            title = line_clean[2:].strip()
            break
            
    return {
        "title": title,
        "filename": input_path.name,
        "ext": input_path.suffix.lower(),
        "text": content,
    }

def main():
    parser = argparse.ArgumentParser(description="Convert documents to Markdown with MarkItDown")
    parser.add_argument("--input", "-i", required=True, help="Path to input document")
    parser.add_argument("--output", "-o", help="Optional output Markdown file path")
    parser.add_argument("--json", action="store_true", help="Output JSON structure with metadata")
    
    args = parser.parse_args()
    input_file = Path(args.input)
    
    try:
        data = convert_document(input_file)
    except Exception as err:
        sys.stderr.write(f"Error: {err}\n")
        sys.exit(1)
        
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(data["text"], encoding="utf-8")
        
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif not args.output:
        print(data["text"])

if __name__ == "__main__":
    main()
