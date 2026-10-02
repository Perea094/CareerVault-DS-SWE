# Background Expansion Findings — 2026-09-15

**Date:** September 15, 2026  
**Author / Processor:** Antigravity AI  
**Scope:** Integration of user verification interview, 5th-semester academic course notes, Ollama model inventory, project repositories, and startup leadership history.

---

## 1. Academic Status & 5th Semester Coursework (Fall 2026)

* **Institution:** Tecnológico de Monterrey, Campus Querétaro
* **Current Phase:** 5th Semester (En curso, Agosto – Diciembre 2026)
* **Program:** Doble Titulación en Ingeniería en Ciencia de Datos y Matemáticas
* **GPA:** 94/100 acumulado (sin cambios pendientes de cierre de semestre)
* **Becas & Distinciones:** Beca de Excelencia Académica Tec, Beca Fundación TELMEX, Programa de Alto Rendimiento Académico (PARA).

### Detalle de Materias Cursadas en 5to Semestre:
1. **Inteligencia Artificial Generativa (`007-Inteligencia artificial generativa`)**:
   - *Arquitecturas:* Transformers profundos, Modelos de Lenguaje Grandes (LLMs).
   - *Fine-Tuning:* PEFT (Parameter-Efficient Fine-Tuning), LoRA, QLoRA, SFT (Supervised Fine-Tuning), curación y limpieza de datasets de instrucción.
   - *RAG & Búsqueda Semántica:* Espacios vectoriales, embeddings densos, cálculo de similitud coseno, bases de datos vectoriales y pipelines de Retrieval-Augmented Generation.
   - *Frameworks:* Hugging Face Transformers, PEFT, TRL, LangChain, LlamaIndex.
   - *Prompt Engineering:* Zero-Shot, Few-Shot, Chain-of-Thought (CoT), ReAct, system prompts dinámicos.
2. **Análisis de Métodos de Razonamiento e Incertidumbre (`001-Análisis de métodos...`)**:
   - Inferencia bayesiana, distribuciones a priori conjugadas, Empirical Bayes.
   - Modelos probabilísticos gráficos, Cadenas de Markov, Modelos Ocultos de Markov (HMM).
   - Algoritmos de inferencia y aprendizaje: Forward-Backward, Algoritmo de Viterbi, Expectation-Maximization (EM) y Baum-Welch.
3. **Aplicación de Métodos Multivariados en Ciencia de Datos (`005-Aplicación de métodos...`)**:
   - Análisis de Componentes Principales (PCA / ACP): descomposición en valores y vectores propios, interpretación geométrica, reducción dimensional.
   - Distribución normal multivariada, matriz de covarianza/correlación, distancia de Mahalanobis, transformaciones afines.
   - Regresión lineal múltiple, selección de variables y ANOVA con variables categóricas.
4. **Optimización Estocástica (`003-Optimización estocástica`)**:
   - Programación lineal, método simplex, procesos estocásticos y optimización bajo incertidumbre.
5. **Aplicación de Criptografía y Seguridad (`006-Aplicación de criptografía...`)**:
   - Criptografía aplicada, seguridad de sistemas e infraestructura criptográfica.
6. **Formación Integral:**
   - `002-Guitarra` (teoría y práctica instrumental).
   - `004-De Prometeo a Marvel` (análisis sociocultural y literatura).

---

## 2. Proyectos Técnicos & Métricas Verificadas

### 1. Street Fighter II RL Agent (LEIA)
* **GitHub:** [LEIA-qro/street_fighter](https://github.com/LEIA-qro/street_fighter) (Autores: Felipe, Diego Perea, Santiago + LEIA, cerrado 2026-09-11)
* **Algoritmo Campeón:** **Ape-X DQN distribuido** con arquitectura **QR-DQN Dueling** (red quantile regression dueling con espacio de 72 acciones discretas).
* **Ingeniería de Sistemas & Flota Distribuida:**
  - Desacoplamiento total: 1 *Learner* central con Replay Priorizado corriendo en máquina GPU (`apex_learner.py`) y múltiples *Actores* distribuidos en una flota comunicados vía **HTTP sobre Tailscale** (`apex_actor.py`).
  - Eficiencia de cómputo: Convergencia con **~50 veces menos cómputo** que el mejor modelo de PPO del proyecto.
* **Dual Backend con Contrato v4 Unificado:**
  - Backend headless en Linux/WSL2 sobre **stable-retro (`libretro`)**, alcanzando **~3,700 FPS por proceso**.
  - Backend en Windows sobre **BizHawk** con puente TCP en *lock-step* leyendo directamente la WRAM big-endian para evaluación visual y PvP humano vs IA.
  - Validación de paridad bit a bit con contrato v4 (23 floats × 4 frames apilados) y suite de 630 pruebas en `pytest`.
* **Métricas Clave de Rendimiento (Juego Resuelto):**
  - **100% de victorias** en dificultades 1 a 4; **99.0%** en dificultades 5 y 6; **97.9%** en dificultad 7; **93.8%** en dificultad 8 ($n=768$).
  - **~90% de win rate** en peleas completas al mejor de 3 rondas en la dificultad máxima (**Nivel 8**) contra los 12 rivales ($n=360$).
  - Comportamiento emergente: Modulación táctica de combate terrestre (`air_frac` disminuyó de 0.45 a 0.20) para contrarrestar ataques anti-aéreos en dificultades altas.

### 2. DAVE — Driver Attention & Vigilance Engine (Automotive Edge AI & IoT DMS)
* **GitHub:** [LEIA-qro/Attention-Algorithm](https://github.com/LEIA-qro/Attention-Algorithm)
* **Premio:** **1er Lugar en Expo Ingenierías** (Tec de Monterrey).
* **Dominio:** Sistema integral de monitoreo de atención y fatiga del conductor (*Driver Monitoring System - DMS*) en cabina de vehículos.
* **Pipeline de Visión Computacional en el Borde:**
  - Inferencia facial con **MediaPipe Face Landmarker v2 con blendshapes** (malla 3D de 478 puntos de referencia).
  - Cálculo de métricas fisiológicas y biomecánicas en tiempo real: EAR (*Eye Aspect Ratio* para parpadeo y somnolencia), MAR (*Mouth Aspect Ratio* para bostezos), estimación de *head pose* 3D (pitch, yaw, roll) y seguimiento de mirada (*iris gaze tracking*).
  - Preprocesamiento robusto para cabina vehicular nocturna/contrastada: ecualización CLAHE y corrección gamma adaptativa.
  - Detección de distracciones en cabina (teléfonos celulares, manos fuera del volante) mediante integración de **YOLOv8** (`yolov8n`).
* **Despliegue & Aceleración en Hardware:**
  - Red neuronal entrenada y evaluada sobre datasets estándar (DMD-Distraction, DMD-Drowsiness, UTA-RLDD, AUC-V2).
  - Exportación a formato **ONNX** (`driver_state_net.onnx`) y ejecución acelerada en el chip NPU **Hailo-8** (26 TOPS) acoplado a **Raspberry Pi 5**, alcanzando inferencia en tiempo real a tasa nativa de **~30 FPS** (29.76 FPS).
  - Buffer circular en memoria (`ring buffer`) para capturar ventanas temporales completas pre y post-evento crítico con generación automática de clips probatorios (`clip_writer.py`).
* **Plataforma IoT Cloud & Dashboard:**
  - Backend en **FastAPI** contenerizado en Docker para ingesta telemática de viajes, almacenamiento de clips y logs de auditoría.
  - Dashboard web en **React + TypeScript + Vite + Tailwind CSS** con vista de HUD para conductor con advertencias sonoras y vista de monitoreo de flotas con mapa interactivo y gráfico temporal de nivel de atención (*AttentionTrace*).

### 3. Aristor Consultoría — Prácticas Profesionales
* **Rol:** Analista de Datos (Mayo 2025 – Septiembre 2025).
* **Impacto:** Creación de un programa de análisis geoespacial para la identificación automatizada de zonas comerciales viables para apertura y expansión de sucursales de restaurantes y servicios en Querétaro, consumiendo microdatos geoestadísticos del INEGI.

---

## 3. Toolstack Local de IA & Modelos Cuantizados

Inventario verificado directamente mediante CLI (`ollama ls`):
* **Modelos Cuantizados de Alta Gama:**
  - `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q2_K_XL` (10 GB)
  - `hf.co/unsloth/Qwen3.8-27B-GGUF:UD-IQ3_XXS` (11 GB)
  - `qwen3.8:latest` (17 GB)
  - `gemma4:26b-64k` (17 GB) y `gemma4:26b` (17 GB)
  - `gemma4:12b-128k` (7.6 GB) y `gemma4:12b` (7.6 GB)
  - `ornith-1.5:9b` (6.6 GB) y `qwen3.5:9b` (6.6 GB)
* **Harnesses & Entornos:**
  - Experiencia en ejecución local y orquestación con Ollama y Open WebUI.
  - Uso activo de herramientas agénticas: **Claude Code**, **OpenCode**, **Antigravity**.
  - Enfoque activo: Comprensión y diseño de flujos agénticos (*agentic workflows*); despliegue cloud previsto como siguiente paso formativo.

---

## 4. Liderazgo, Emprendimiento & Retos Corporativos

### 1. AB-Tec (Startup de Cuidado y Salud)
* **Rol:** **CEO y Co-Fundador** (5 miembros).
* **Logros:** Formulación química original, manufactura y comercialización de geles antibacteriales dentro de la comunidad universitaria. Operación comercial exitosa hasta pausar el proyecto para priorizar la exigencia académica del doble grado.

### 2. Reto Corporativo Databricks: "From the Kitchen to the Cloud" (13-Week Data Challenge)
* **Organización:** Powered by Sun Holdings, en alianza con Databricks, Inc. y Tec de Monterrey.
* **Fecha:** Septiembre 14 – Diciembre 11, 2026.
* **Fases:**
  - Semanas 1–4: Capacitación intensiva y obtención de insignias de certificación oficial de Databricks.
  - Semanas 5–12: Implementación guiada con mentoría técnica sobre datos de transacciones reales multi-sucursal.
  - Semana 13: Pitch final por el premio de $1,500 USD.
* **Temática / Reto:** Analítica avanzada sobre datos reales de restaurantes (Applebee's — Detección de fraude con agentes de IA y pipelines masivos; o Taco Bueno — Analítica de promociones, pricing y canibalización de menú).
