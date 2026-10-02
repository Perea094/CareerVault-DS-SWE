---
created: 2026-09-15
updated: 2026-09-15
type: cv-evaluation
cv_target: "002-cv/general-cv.md"
job_target: "004-work-opportunities/Intern-Generative AI Research Engineer.md"
score: 64
verdict: "Borderline"
tags:
  - cv-review
  - recruiter-audit
  - cotiviti
  - genai-internship
---

# Recruiter Audit: Cotiviti — Intern, Generative AI Research Engineer

## 1. Executive Screening Verdict
- **Overall Score**: 64/100
- **Recruiter Verdict**: **Borderline / High Screening Risk**
- **Estimated Screen Time**: 6 seconds (Immediate scrutiny on location, visa, and degree level)
- **Top Positive Signal**: High academic rigor (GPA 94/100, scholarships, PARA program), strong foundational math/ML, and hands-on PyTorch/RL and edge AI projects.
- **Top Vulnerability**: Non-US location without US work authorization for a "US-Remote" posting, plus education gap (JD prefers PhD / Advanced Degree vs. active B.S. candidate).

---

## 2. Pillar Scorecard Breakdown

| Evaluation Pillar | Weight | Score (0–100) | Weighted Score | Recruiter Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Quantifiable Impact (XYZ Formula)** | 30% | 58 | 17.4 | Only 12% of bullets contain hard numbers/metrics. Technical accomplishments are described, but measurable business/system outcomes are sparse. |
| **Technical Depth & Evidence** | 25% | 72 | 18.0 | Strong on PyTorch, RL (PPO/SAC), Hailo-8 edge AI, and algorithms, but missing explicit mentions of RAG, vector databases, and cloud infrastructure (AWS/Azure). |
| **Signal-to-Noise & Prioritization** | 20% | 68 | 13.6 | Toy academic projects (e.g., Pokémon simulation in Python, C++ racing game) dilute page real estate that should feature GenAI, LLM architectures, and data pipelines. |
| **ATS Parseability & Format** | 15% | 85 | 12.8 | Clean single-column structure, standard section headers, clean typography. High ATS readability. |
| **Distinguishing Leadership / Awards** | 10% | 82 | 8.2 | Co-founding LEIA, teaching RL workshops to ~30 students, winning 1st place at Expo Ingenierías, and TELMEX Scholarship provide solid standout proof. |
| **Total** | **100%** | | **70.0 / 100** *(Raw ATS Metric Score: 55.3)* | **Weighted Screening Score: 64/100** |

---

## 3. Job Description Gap & Keyword Analysis

- **Target Job**: Cotiviti — Intern, Generative AI Research Engineer (Healthcare Informatics)
- **Keyword Coverage**: ~20% of core JD keywords explicitly matched in current CV text.

### Matched Critical Requirements
- [x] Hands-on Python & PyTorch experience
- [x] Machine Learning & Deep Learning model training
- [x] Generative AI familiarity (Ollama listed in tools)
- [x] Strong communication & collaboration (LEIA workshop organizer, academic mentor)

### Critical Gaps & Missing Keywords
- [ ] **RAG & Vector Databases**: JD explicitly emphasizes *"Hands-on experience with LLM/RAG models and vector databases"*. Current CV lists no vector DBs (e.g., Chroma, FAISS, Pinecone) or RAG architectures.
- [ ] **Cloud Services (AWS / Azure)**: Listed as a requirement for building data pipelines for ML solutions. Not present on CV.
- [ ] **Healthcare / Biomedical Informatics**: Zero healthcare framing in project bullets.

### Eligibility & Constraints Check (`001-background/preferences.md`)
- **Location & Visa**: ⚠️ **CRITICAL FLAG**. JD specifies `Job Locations US-Remote`. Diego is based in Querétaro, Mexico with no US work authorization. Unless Cotiviti supports international contractor agreements or has a Mexican entity (EOR), automated ATS filters may reject this application outright.
- **Hours**: Compliant. Posting permits 20–40 hours/week (Diego prefers 20–30 hours/week).
- **Compensation**: $32–$40/hr exceeds the candidate's $20/hr minimum threshold.
- **Education Tier**: JD states *"Currently pursuing or recently completed an advanced degree with preference of a PhD"*. Diego is in 4th semester of undergraduate studies.

---

## 4. Section-by-Section Recruiter Critique

### Education
- **What works**: GPA 94/100, TELMEX Foundation Scholarship, and PARA membership immediately validate raw intellectual caliber.
- **Improvement**: Move Relevant Coursework to highlight *Machine Learning, Probability & Statistics, Data Structures* upfront, de-emphasizing non-GenAI coursework.

### Experience
- **Aristor Consultoría**: Good practical data experience, but needs concrete impact metrics.
- **LEIA**: High leadership signal. Needs to emphasize LLM/Generative AI workshop content rather than just RL.

### Projects
- **Cut/Deprioritize**: Pokémon simulation and C++ racing game should be removed immediately from any application for an AI research engineering role.
- **Promote/Enhance**: Elevate Ollama, Hailo-8 edge AI, and any LLM fine-tuning or evaluation experiments.

---

## 5. Actionable Bullet Point Rewrites (Before vs. After)

### Aristor Consultoría (Data Analyst Intern)
- **Before**: *"Collaborated on integrating predictive models applied to market intelligence"*
- **Recruiter Critique**: Passive verb ("collaborated on"), zero metrics, no tech stack mentioned.
- **Recommended Rewrite**: *"Engineered predictive spatial models analyzing 10k+ commercial datapoints via INEGI databases, delivering targeted demographic expansion recommendations for 5+ restaurant enterprise clients."*

### LEIA (Co-Founder & Workshop Organizer)
- **Before**: *"Co-planned and executed two introductory AI workshops teaching reinforcement learning (Q-learning, PPO) to ~30 students"*
- **Recruiter Critique**: Good metric, but could highlight curriculum design and hands-on ML implementation.
- **Recommended Rewrite**: *"Architected and delivered hands-on AI curriculum covering reinforcement learning (PPO, Q-learning) and LLM fundamentals for 30+ engineering students, achieving 1st place recognition at Expo Ingenierías."*

### DAVE Surveillance System (Hailo-8 Edge AI)
- **Before**: *"Built object-detection camera surveillance system with custom frame ring-buffering and pre/post-trigger recording windows"*
- **Recruiter Critique**: Descriptive of function, but misses hardware throughput and latency achievements.
- **Recommended Rewrite**: *"Deployed real-time edge AI surveillance pipeline on Raspberry Pi 5 with Hailo-8 acceleration (26 TOPS), implementing circular frame ring-buffers to record pre/post-event incident windows at 30+ FPS."*

---

## 6. Background Vault Recommendations (`001-background/`)

1. **Surface GenAI / LLM Artifacts**: Mine `001-background/projects/` for any prompt engineering, LLM benchmark evaluations, or synthetic data generation scripts to bridge the JD's RAG/LLM requirement.
2. **Prioritize Cloud ML Exposure**: If any AWS/GCP/Azure lab work exists in academic coursework, document it in `001-background/experiences/` and feature it in the technical skills block.
3. **Application Recommendation**: Only submit if the application form allows selecting Mexican residency or if contacting the hiring manager directly to verify international remote contractor eligibility.
