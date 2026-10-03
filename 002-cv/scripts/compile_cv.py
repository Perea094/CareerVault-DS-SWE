#!/usr/bin/env python3
"""
Automated LaTeX CV Compiler with High-Resolution PNG Preview Generation.
Detects available LaTeX compilers (tectonic, pdflatex, xelatex, latexmk),
compiles .tex resumes to PDF, and renders a page 1 PNG snapshot for Obsidian embedding.
Supports CLI, JSON output for AI agents, and custom output directories.
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Tuple, Union

try:
    import pypdfium2
except ImportError:
    pypdfium2 = None

SUPPORTED_COMPILERS = ["tectonic", "pdflatex", "xelatex", "latexmk"]


def detect_latex_compiler() -> Optional[str]:
    """Detects first available LaTeX compiler in PATH."""
    for compiler in SUPPORTED_COMPILERS:
        if shutil.which(compiler):
            return compiler
    return None


def resolve_tex_path(tex_file: Union[str, Path]) -> Path:
    """
    Resolves tex_file path checking working directory, vault root, or 002-cv directory.
    """
    path = Path(tex_file)
    if path.exists():
        return path

    vault_root = Path(__file__).resolve().parent.parent.parent
    if (vault_root / path).exists():
        return vault_root / path

    cv_dir = Path(__file__).resolve().parent.parent
    if (cv_dir / path).exists():
        return cv_dir / path

    return path


def build_compile_command(compiler: str, tex_file: Path, output_dir: Path) -> list:
    """Builds appropriate CLI arguments for the detected compiler."""
    tex_path = str(Path(tex_file).resolve())
    out_path = str(Path(output_dir).resolve())
    
    if compiler == "tectonic":
        return [compiler, "--outdir", out_path, tex_path]
    elif compiler in ["pdflatex", "xelatex"]:
        return [
            compiler,
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={out_path}",
            tex_path
        ]
    elif compiler == "latexmk":
        return [
            compiler,
            "-pdf",
            f"-outdir={out_path}",
            "-interaction=nonstopmode",
            tex_path
        ]
    else:
        raise ValueError(f"Unsupported compiler: {compiler}")


def generate_preview_image(pdf_path: Path, output_png: Path = None, dpi: int = 150) -> Path:
    """Renders the first page of the PDF to a high-resolution PNG using pypdfium2."""
    if pypdfium2 is None:
        raise RuntimeError("pypdfium2 is not installed. Install it with: pip install pypdfium2")
    
    pdf_path = Path(pdf_path)
    if output_png is None:
        output_png = pdf_path.with_suffix(".png")
    else:
        output_png = Path(output_png)
        
    doc = pypdfium2.PdfDocument(str(pdf_path))
    if len(doc) == 0:
        raise ValueError(f"PDF document {pdf_path} contains 0 pages.")
        
    page = doc[0]
    # Standard 72 DPI base scale * (dpi / 72)
    scale = dpi / 72.0
    image = page.render(scale=scale).to_pil()
    image.save(str(output_png), format="PNG")
    return output_png


def compile_resume(
    tex_file: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    generate_png: bool = True,
    dpi: int = 150
) -> Tuple[Path, Optional[Path]]:
    """Orchestrates compilation and preview generation."""
    resolved_tex = resolve_tex_path(tex_file)
    if not resolved_tex.exists():
        raise FileNotFoundError(f"LaTeX file not found: {resolved_tex}")
        
    if output_dir is None:
        target_out_dir = resolved_tex.parent
    else:
        target_out_dir = Path(output_dir)
    target_out_dir.mkdir(parents=True, exist_ok=True)
    
    compiler = detect_latex_compiler()
    if not compiler:
        raise RuntimeError(
            "No LaTeX compiler found in PATH. Please install Tectonic or MiKTeX.\n"
            "Quick install (PowerShell): winget install MiKTeX.MiKTeX"
        )
        
    cmd = build_compile_command(compiler, resolved_tex, target_out_dir)
    print(f"[INFO] Compiling {resolved_tex.name} using {compiler}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[ERROR] LaTeX compilation failed:\n{result.stderr or result.stdout}", file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd, output=result.stdout, stderr=result.stderr)
        
    pdf_name = resolved_tex.stem + ".pdf"
    pdf_path = target_out_dir / pdf_name
    print(f"[SUCCESS] PDF generated at: {pdf_path}")
    
    png_path = None
    if generate_png:
        try:
            png_path = generate_preview_image(pdf_path, dpi=dpi)
            print(f"[SUCCESS] PNG preview generated at: {png_path}")
        except Exception as e:
            print(f"[INFO] Skipping optional PNG preview ({e}). PDF compilation succeeded.", file=sys.stderr)
            
    return pdf_path, png_path


def main():
    parser = argparse.ArgumentParser(description="Compile LaTeX Resume to PDF and PNG preview")
    parser.add_argument("tex_file", nargs="?", default="002-cv/template.tex", help="Path to .tex file")
    parser.add_argument("--output-dir", "-o", default=None, help="Directory to place PDF and PNG")
    parser.add_argument("--no-preview", action="store_true", help="Skip PNG preview generation")
    parser.add_argument("--dpi", type=int, default=150, help="DPI for PNG preview (default: 150)")
    parser.add_argument("--preview-only", action="store_true", help="Only generate PNG from existing PDF")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON status for AI agents")
    
    args = parser.parse_args()
    tex_path = resolve_tex_path(args.tex_file)
    compiler = detect_latex_compiler()
    
    if args.preview_only:
        pdf_path = tex_path.with_suffix(".pdf")
        if not pdf_path.exists():
            if args.json:
                print(json.dumps({"success": False, "error": f"PDF not found: {pdf_path}"}))
            else:
                print(f"[ERROR] PDF not found: {pdf_path}", file=sys.stderr)
            sys.exit(1)
        try:
            png = generate_preview_image(pdf_path, dpi=args.dpi)
            if args.json:
                print(json.dumps({"success": True, "preview_png": str(png.resolve())}))
            else:
                print(f"[SUCCESS] Preview saved to: {png}")
            sys.exit(0)
        except Exception as e:
            if args.json:
                print(json.dumps({"success": False, "error": str(e)}))
            else:
                print(f"[ERROR] Failed to generate PNG preview: {e}", file=sys.stderr)
            sys.exit(1)
        
    try:
        pdf_path, png_path = compile_resume(
            tex_file=tex_path,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            generate_png=not args.no_preview,
            dpi=args.dpi
        )
        if args.json:
            print(json.dumps({
                "success": True,
                "compiler": compiler,
                "pdf_path": str(pdf_path.resolve()),
                "png_path": str(png_path.resolve()) if png_path else None
            }))
    except Exception as e:
        if args.json:
            print(json.dumps({
                "success": False,
                "compiler": compiler,
                "error": str(e)
            }))
        else:
            print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
