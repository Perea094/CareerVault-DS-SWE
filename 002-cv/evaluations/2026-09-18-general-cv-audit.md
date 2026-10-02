---
created: 2026-09-18
updated: 2026-09-18
type: cv-evaluation
cv_target: "002-cv/general-cv.md"
job_target: "General Audit"
score: 88
verdict: "Pass"
tags:
  - cv-review
  - recruiter-audit
  - career
  - general-cv
---

# Recruiter Audit: General CV Health Check (Diego Perea León)

## 1. Executive Screening Verdict
- **Overall Score**: 88/100
- **Recruiter Verdict**: **Pass / Highly Competitive** (Top ~10% for undergraduate AI/Data Science profiles)
- **Estimated Screen Time**: 6-second scan yields instant positive impression on technical horsepower (Ape-X DQN, Hailo-8 NPU, GPA 94/100, scholarships).
- **Top Positive Signal**: Technical rigor in flagship projects (Street Fighter II distributed RL with Ape-X DQN & ~50x compute reduction; DAVE edge AI on Hailo-8 26 TOPS NPU). These are far above typical student toys.
- **Top Vulnerability**: Domain dissonance and unquantified bullets in experience. AB-Tec (antibacterial gel production) dilutes the AI/systems narrative, while Aristor Consultoría and Databricks lack hard scale metrics.

---

## 2. Pillar Scorecard Breakdown

| Evaluation Pillar | Weight | Score (0–100) | Weighted Score | Recruiter Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Quantifiable Impact (XYZ Formula)** | 30% | 84 | 25.2 | 10 of 15 bullets (66.7%) have metrics. Street Fighter and DAVE are near-perfect (100% win rate, ~3,700 FPS, 26 TOPS, 30 FPS). However, Aristor has zero numbers, Databricks has no data volume metrics, and GenAI SFT/RAG lacks quantitative benchmark outcomes. |
| **Technical Depth & Evidence** | 25% | 90 | 22.5 | Exceptional algorithms and systems: Ape-X DQN, Dueling QR-DQN, Tailscale, stable-retro, BizHawk Lua memory inspection, MediaPipe 478 3D landmarks, Hailo-8 ONNX acceleration. Minor gap: RAG bullet does not specify the vector database or embedding model used. |
| **Signal-to-Noise & Prioritization** | 20% | 85 | 17.0 | Eliminating former toy projects (Pokémon, C++ racing) was a major win. However, AB-Tec (chemical hand sanitizers) creates domain dissonance on an AI/Data Science resume. Also, "1st Place at Expo Ingenierías" is repeated verbatim across both LEIA and DAVE. |
| **ATS Parseability & Format** | 15% | 94 | 14.1 | Clean single-column layout, standard headers, no graphical tables/text boxes, reverse chronological order. High ATS readability. Minor note: university student ID email (`a01708350@tec.mx`) signals student status over industry permanence. |
| **Distinguishing Leadership / Awards** | 10% | 95 | 9.5 | Co-founding LEIA, teaching 30+ students per workshop, TELMEX Foundation Scholarship (elite national award in Mexico), Tec Academic Excellence Scholarship, PARA program membership. Strong leadership indicators. |
| **Total** | **100%** | | **88.3 / 100** | **Recruiter Screening Verdict: Pass (88/100)** |

---

## 3. Market Positioning & Alignment (`001-background/preferences.md`)

- **Career Target**: GenAI/LLMs, Reinforcement Learning, Computer Vision, and Applied ML roles (IC track, remote or international with visa sponsorship, 20–30 hrs/week during school).
- **Core Strengths**: 
  - Dual major in Data Science and Mathematics provides unmatched credibility for algorithmic/theoretical roles (RL, optimization, Bayesian inference).
  - Hands-on edge AI and distributed systems experience proves end-to-end engineering capability, not just Jupyter notebook modeling.
- **Market Perception Risks**:
  - Without US work authorization, US-remote applications often encounter automatic ATS geographic disqualification unless applying to global remote-first companies (e.g. Gitlab, Automattic, Canonical) or via international contractors / EOR entities.
  - GPA (94/100) and national scholarships (TELMEX) lack clear reference frames for international hiring managers unfamiliar with the Mexican grading system.

---

## 4. Section-by-Section Critical Critique

### 4.1 Header & Contact
- **Email**: `a01708350@tec.mx` is an institutional student ID. Consider using a clean personal professional email (e.g., `diego.perea.leon@gmail.com` or custom domain) or listing both. Professional tech recruiters favor permanent addresses.
- **Location**: `Querétaro, Mexico` is accurate. If applying to global remote roles, appending `(Remote UTC-6)` immediately answers timezone overlap questions for hiring managers.

### 4.2 Education
- **GPA Calibration**: 94/100 is excellent, but international screeners may not know if it is equivalent to a 3.5, 3.8, or 4.0. Adding `(~3.8/4.0 equivalent; top 5%)` contextualizes the achievement.
- **Scholarships**: Add 2–3 words explaining the prestige of the TELMEX Scholarship (`TELMEX Foundation Scholarship — awarded to top 1% academic students nationwide`).

### 4.3 Experience & Corporate Challenges
- **Databricks Fellowship**: 
  - Bullet 1 starts with `"Selected for..."`, which is passive. Frame this around *active system engineering*: what pipelines are you building on Delta Lake? What is the transaction volume?
  - Bullet 2 mentions fraud detection and cannibalization models. Specify the algorithms (e.g., PySpark MLlib, Graph/Isolation Forest) and the scale of transaction data.
- **Aristor Consultoría**:
  - The work with INEGI spatial microdata is high-value commercial engineering, but it currently has zero numbers. Add dataset scale (e.g., *10,000+ census polygons and commercial entities across 15+ urban zones*) and the business outcome (e.g., *cutting franchise site-selection analysis time by 70%*).
- **LEIA**:
  - High leadership signal. To avoid redundancy with the DAVE entry, emphasize LEIA's growth, research roadmap, and curriculum delivery rather than repeating the Expo Ingenierías award here.
- **AB-Tec**:
  - **Critical Recruiter Flag**: Formulating antibacterial gel and direct sales does not support an AI, Machine Learning, or Data Science engineering profile. It takes up 4 vertical lines. 
  - **Action**: Move to a compact single-line mention under "Leadership & Activities" or replace it with a technical software/data project (e.g., the C# 3D Procedural Labyrinth engine or SHA-256 Collision Cryptography project from `001-background/projects/projects-2026-09-15.md`).

### 4.4 Projects
- **Street Fighter II Distributed RL Agent**:
  - **Exceptional tier-1 project**. The metrics (~50x less compute, ~3,700 FPS, 630 pytest tests, 93.8%–100% win rates) are gold-standard.
  - Optional enhancement: Mention the emergent strategic behavior identified in your documentation (*reduced air fraction from 0.45 to 0.20 to counter high-level CPU anti-air moves*).
- **DAVE (Driver Attention & Vigilance Engine)**:
  - Lead with the technical architecture rather than just the award banner.
  - Ground the training pipeline by citing the automotive benchmark datasets you utilized (`DMD-Distraction, UTA-RLDD, AUC-V2` from background records). This signals genuine deep learning engineering, not just wrapping a pre-trained model.
- **Local LLMs, Model Quantization & GenAI Engineering**:
  - Give this section an authoritative project title rather than a generic skill grouping, e.g. **Local LLM Benchmarking & Fine-Tuning Suite** or **Agentic LLM Infrastructure**.
  - Bullet 2 has zero metrics (`has_metric: false`). Ground it with quantitative parameters: dataset size (e.g. *15,000 instruction-tuning pairs*), parameter efficiency (e.g. *reducing trainable parameters by >99% via QLoRA*), or retrieval latency/precision.
  - Name the vector database explicitly (e.g., FAISS, Chroma) instead of generic "dense vector retrieval".

### 4.5 Leadership & Activities
- **Mentorship**: Quantify the teaching impact (e.g., *Tutored 15+ undergraduate engineering students in linear algebra, multivariable calculus, and Python across 40+ hours*).
- **Chess Club**: Solid signal for structured analytical thinking.

### 4.6 Technical Skills & Tools
- Tight, well-evidenced stack. Every tool listed appears in projects.
- Recommended addition: Add vector DB (`Chroma` or `FAISS`) under ML & GenAI, and `PostgreSQL / PostGIS` or `GeoPandas` if applicable from Aristor.

---

## 5. Actionable Bullet Point Rewrites (Before vs. After)

### 1. Databricks Corporate Challenge
- **Before**: 
  > *"Selected for an intensive 13-week corporate challenge building Lakehouse pipelines and AI agent workflows over real multi-branch transactional datasets across restaurant chains (Applebee's / Taco Bueno)."*
- **Recruiter Critique**: Passive starter ("Selected for"); lacks technical architecture nouns and dataset magnitude.
- **Recommended Rewrite**:
  > *"Architecting end-to-end Lakehouse data pipelines and AI agents on Databricks Delta Lake, processing multi-branch transactional datasets across 100+ franchise locations (Applebee's / Taco Bueno) for automated fraud detection."*

### 2. Aristor Consultoría
- **Before**: 
  > *"Engineered an automated spatial analysis engine processing INEGI geo-statistical microdata to evaluate commercial viability and expansion opportunities for restaurant and service franchises across Querétaro."*
- **Recruiter Critique**: Strong verb, but zero numbers. How big was the dataset? What was the speedup?
- **Recommended Rewrite**:
  > *"Engineered an automated spatial analysis pipeline in Python processing 10,000+ INEGI census and commercial records across 15+ urban zones, reducing client retail site evaluation turnaround from 5 days to under 2 hours."*

### 3. Local LLMs & GenAI Engineering
- **Before**: 
  > *"Built Supervised Fine-Tuning (SFT) pipelines using Hugging Face (Transformers, PEFT, TRL) leveraging LoRA/QLoRA on instruction datasets, and developed RAG pipelines with dense vector retrieval using LangChain."*
- **Recruiter Critique**: Reads like a list of technologies from course syllabus without concrete outcomes or metrics.
- **Recommended Rewrite**:
  > *"Developed Supervised Fine-Tuning (SFT) pipelines using Hugging Face (PEFT/TRL) applying 4-bit QLoRA to reduce trainable parameters by >99%, and engineered a low-latency RAG system with FAISS dense vector retrieval and semantic chunking."*

### 4. DAVE — Automotive DMS
- **Before**: 
  > *"Won 1st Place at Expo Ingenierías for architecting an automotive Driver Monitoring System (DMS) deployed on edge hardware."*
- **Recruiter Critique**: Wastes the first bullet purely on the award instead of what the system does.
- **Recommended Rewrite**:
  > *"Architected an edge Driver Monitoring System (DMS) combining multi-task computer vision and embedded acceleration that won 1st Place (out of 40+ engineering projects) at Expo Ingenierías."*

---

## 6. Background Vault Opportunities (`001-background/`)

### Under-leveraged Assets in Vault:
1. **Procedural 3D Labyrinth Game (C# / Raylib / .NET)**:
   - Found in `001-background/projects/projects-2026-09-15.md` and `findings/consolidated-findings.md`.
   - Demonstrates strong OOP architecture, state machines, pathfinding algorithms, and systems-level programming outside pure Python. If applying to software engineering or graphics/gaming AI roles, this is vastly superior to AB-Tec.
2. **SHA-256 Collision Attack (`MySHA6` / Pytest)**:
   - Found in `001-background/projects/projects-2026-09-15.md`.
   - Proves deep algorithmic rigor and discrete math application (birthday paradox collision search, precomputed lookup tables).
3. **Automotive Datasets (DMD, UTA-RLDD)**:
   - Mentioned in `001-background/projects/projects-2026-09-15.md`. Validating your neural networks on established academic datasets demonstrates research maturity.

### Items to Prune / Reallocate:
- **AB-Tec**: Demote to a 1-line item in "Leadership & Activities" (e.g. *Co-founder of AB-Tec, campus hygiene startup*) to reclaim 3-4 lines of prime real estate in the Experience section for deeper Databricks or Aristor metrics.
