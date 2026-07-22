# ToolKit
### Unified Document Conversion, Image Processing & Developer Utility Platform

**Version:** 0.1 (Pre-Release / MVP Planning)
**Document Type:** Product & Technical Overview
**Audience:** Engineering teams, technical stakeholders, self-hosting adopters

---

## 1. Executive Summary

ToolKit is a self-hostable, full-stack web platform that consolidates document conversion, image processing, and developer utility tools into a single, unified application. It is designed for developers, designers, and technical teams who currently rely on a fragmented ecosystem of third-party web services to perform routine file and data transformations.

Rather than distributing sensitive files across numerous external tools — each with its own privacy policy, upload limits, and paywall — ToolKit centralizes this functionality behind a single, self-hosted deployment. All processing is performed server-side within infrastructure the operator controls, eliminating third-party data exposure, unpredictable file-size restrictions, and recurring subscription costs.

The platform is built on a modern, production-grade stack: a FastAPI backend for high-performance asynchronous processing, and a Next.js frontend delivering a polished, responsive user experience. Docker Compose orchestration allows the entire system to be deployed with a single command, making it suitable for individual developers, internal engineering tools, or team-wide internal platforms.

---

## 2. Problem Statement

Technical teams routinely need to:

- Convert between document formats (Markdown, PDF, DOCX, HTML, LaTeX)
- Manipulate and optimize images (compression, resizing, background removal, format conversion)
- Perform everyday developer tasks (JSON formatting, hashing, encoding, JWT inspection, regex testing)

Today, these tasks are typically handled by a patchwork of unrelated single-purpose web tools. This fragmented approach introduces several recurring problems:

| Problem | Impact |
|---|---|
| Files uploaded to unknown third-party servers | Data privacy and compliance risk |
| Inconsistent or aggressive file-size limits | Workflow interruptions |
| Intrusive, irrelevant ads on unrelated tools | Poor experience, no control over ad quality |
| No unified interface or design language | Context-switching overhead |
| No offline or self-hosted option | Unsuitable for regulated or air-gapped environments |

ToolKit addresses each of these by offering a single, cohesive, self-hosted platform where every tool shares the same infrastructure, security posture, and user experience.

---

## 3. Product Vision

ToolKit aims to become the default internal utility platform for engineering teams — the equivalent of an internal "Swiss Army knife" web service that any team member can rely on without needing to vet external tools for data-handling practices.

Guiding principles:

1. **Privacy by default** — no file or data ever leaves the operator's own infrastructure.
2. **Unified experience** — every tool shares consistent design, navigation, and interaction patterns.
3. **Self-hostable and portable** — deployable via Docker Compose in minutes, on any infrastructure.
4. **Extensible architecture** — new tools can be added as isolated modules without disrupting existing functionality.
5. **No artificial limitations** — no paywalls, no forced file-size caps beyond what the operator configures.

---

## 4. Core Feature Groups

### 4.1 Document Tools

| Tool | Description |
|---|---|
| Markdown → PDF | Converts `.md` files into styled, professional PDF documents |
| Markdown → DOCX | Exports Markdown content into editable Word documents |
| DOCX → Markdown | Strips Word-specific formatting down to clean Markdown |
| HTML → PDF | Renders arbitrary HTML (with CSS support) into PDF |
| LaTeX → PDF | Compiles `.tex` source files into PDF via Pandoc |
| PDF Merger | Combines multiple PDF files into a single document |
| PDF Splitter | Extracts specific page ranges from a PDF |
| PDF → Text | Extracts raw text content from PDF files |
| PDF Watermarker | Overlays custom watermarks onto existing PDFs |

### 4.2 Image Tools

| Tool | Description |
|---|---|
| Background Remover | AI-powered background removal, executed locally via an ONNX model (no external API key required) |
| Image Compressor | Reduces file size while preserving visual quality |
| Format Converter | Converts between PNG, JPG, WebP, and GIF |
| Image Resizer | Batch resizing with optional aspect-ratio locking |
| SVG → PNG / PDF | Converts vector SVG graphics into raster or PDF output |
| Grayscale Converter | Converts color images to black and white |
| Image Cropper | Crops images to precise, user-defined dimensions |

### 4.3 Developer Utilities

| Tool | Description |
|---|---|
| JSON Formatter | Pretty-prints, validates, and minifies JSON |
| CSV ↔ JSON | Bidirectional conversion between CSV and JSON |
| Base64 Encoder / Decoder | Encodes and decodes strings or files to/from Base64 |
| Hash Generator | Generates MD5, SHA-1, SHA-256, and SHA-512 hashes |
| JWT Decoder | Inspects and decodes JWT tokens entirely offline |
| Diff Checker | Side-by-side text comparison with change highlighting |
| QR Code Generator | Generates styled QR codes from URLs or arbitrary text |
| Regex Tester | Live regex playground with real-time match highlighting |
| Password Generator | Configurable, cryptographically secure password generator |
| Color Converter | Converts between HEX, RGB, and HSL with live preview |
| Timestamp Converter | Converts between Unix timestamps and human-readable datetimes |
| Word / Character Counter | Provides text statistics and estimated reading time |

---

## 5. Technology Stack

### 5.1 Backend

| Technology | Role |
|---|---|
| Python 3.11 | Core runtime |
| FastAPI | Asynchronous, high-performance REST API framework |
| Uvicorn | ASGI application server |
| pypandoc | Document conversion engine (Pandoc wrapper) |
| python-docx | Reading and writing Microsoft Word files |
| WeasyPrint | HTML/CSS → PDF rendering engine |
| ReportLab | Programmatic PDF generation |
| pypdf | Merging, splitting, and manipulating existing PDFs |
| Pillow | Core image processing library |
| rembg | Local, AI-driven background removal (ONNX runtime) |
| opencv-python-headless | Advanced image processing operations |
| cairosvg | SVG → PNG/PDF rasterization |
| qrcode | QR code generation |
| python-jose | JWT encoding and decoding |
| passlib | Secure password hashing |
| Celery + Redis | Asynchronous task queue for long-running or heavy jobs |

### 5.2 Frontend

| Technology | Role |
|---|---|
| Next.js 14 | React framework with App Router |
| TypeScript | Static typing across the frontend codebase |
| Tailwind CSS | Utility-first styling system |
| shadcn/ui | Accessible, composable UI component library |
| Framer Motion | Animations and page transitions |
| Lucide Icons | Icon system |
| Axios | HTTP client for backend API communication |
| mammoth.js | Client-side DOCX → HTML preview rendering |
| jsPDF | Client-side PDF generation fallback |

### 5.3 Infrastructure

| Technology | Role |
|---|---|
| Docker | Application containerization |
| Docker Compose | Multi-service orchestration |
| Nginx | Reverse proxy and request/file size limiting |
| Redis | Task queue broker and general-purpose cache |
| Pandoc | System-level document conversion binary |

---

<p align="center"><em>Built for developers who value their time and their privacy.</em></p>
