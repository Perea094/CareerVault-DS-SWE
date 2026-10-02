---
created: 2026-10-01
updated: 2026-10-01
type: experience
tags:
  - background
  - experience
  - socio-formador
  - fullstack
  - nextjs
  - typescript
  - logistics
  - fefo
  - sqlite
  - tec-de-monterrey
status: evergreen
---

# Experiencia Profesional, Liderazgo y Proyectos con Socios Formadores — 2026-10-01

## Proyectos de Vinculación con Socios Formadores (Tecnológico de Monterrey)

### Fundación Nutrición y Vida, A.C. (FNVAC - CEDIS Celaya) — Ingeniero de Software Full-Stack & Arquitecto de Solución
*Socio Formador Tec21 | Celaya, Guanajuato & Querétaro, México | Septiembre 2026 – Octubre 2026*  
*Repositorio Oficial:* [Perea094/Food-Inventory-Manager-FNVAC](https://github.com/Perea094/Food-Inventory-Manager-FNVAC)

- **Contexto Institucional & Escala de Impacto:**
  - Colaboré directamente con **Fundación Nutrición y Vida, A.C. (FNVAC)**, uno de los bancos de alimentos más grandes y tecnificados del Bajío mexicano, responsable de rescatar más de **6,100 toneladas de alimento anuales** y repartir más de **314,000 despensas** a comunidades en vulnerabilidad de Guanajuato y Querétaro.
  - Operación respaldada por donantes estratégicos como **Grupo Industrial Cuadritos Biotek** (altos volúmenes de lácteos y bebidas de soya con estricta cadena de frío), agricultores de hortalizas del Bajío y una flota de **3 camiones Torton refrigerados Thermo King**.

- **Problemática Operativa Resuelta:**
  - Diseñé e implementé la solución técnica para sustituir el flujo operativo histórico basado en **hojas de cálculo manuales de Excel**, el cual causaba mermas por caducidad no detectada, riesgos de ruptura en la cadena de frío y sobrecostos logísticos por rutas ineficientes.

- **Arquitectura de Software & Stack Tecnológico:**
  - **Framework Full-Stack:** Next.js 14.2+ (App Router con Server Actions y Route Handlers REST) con TypeScript 5.6 estricto.
  - **Base de Datos & Persistencia:** SQLite local mediante el módulo nativo `node:sqlite` de Node.js, garantizando transacciones ACID, alta resiliencia y cero problemas de compilación binaria C++ (`node-gyp`).
  - **Interfaz & Accesibilidad:** Tailwind CSS 3.4 y Lucide React, con vistas responsivas para andén/patio y estilos dedicados para impresión física de manifiestos (`@media print`).
  - **Geolocalización & Ruteo:** Leaflet 1.9 + OpenStreetMap para visualización interactiva y cálculo de proximidad geográfica mediante algoritmo Haversine, sin dependencias ni costes de APIs comerciales.
  - **Captura Dual:** `html5-qrcode` para escaneo óptico por cámara móvil en patio y listeners continuos con auto-enfoque para pistolas lectoras USB/Bluetooth industriales en andén.
  - **Interoperabilidad:** SheetJS (`xlsx`) para generación y lectura directa de libros de cálculo Excel.
  - **Testing Automatizado:** Suite completa de **177 pruebas automatizadas** en 19 suites utilizando el Test Runner nativo de Node.js (`node:test`), alcanzando 100% de éxito en pruebas unitarias, de integración y flujo operacional E2E completo.

- **Módulos & Contribuciones Técnicas Clave:**
  1. **Control de Inventario FEFO (*First Expired, First Out*):** Tablero reactivo en tiempo real con indicadores KPI de existencias, semaforización automatizada de caducidad (🔴 Crítico ≤ 3 días, 🟡 Atención 4–7 días, 🟢 Estable > 7 días) y segmentación por zonas del almacén (Cámaras Frías vs. Nave de Secos).
  2. **Recepción Rápida y Escaneo en Andén:** Captura continua por código de barras (USB/Cámara), atajos de un toque para recepción de cosechas agrícolas a granel (brócoli, zanahorias, jitomates), modal de catalogación exprés de nuevos productos en <10 segundos y validación preventiva que bloquea el ingreso de alimentos caducados.
  3. **Planificador Inteligente de Rutas & Cadena de Frío:** Motor logístico que evalúa la distancia geográfica desde el CEDIS Celaya hacia comunidades beneficiarias (San Juan de la Vega, Rincón de Tamayo, San Miguel Octopan, Comonfort, etc.), imponiendo el despacho obligatorio en camión Torton refrigerado con Thermo King (4°C) para cargas con lácteos y perecederos, y Camionetas de 3.5T para secos, controlando límites de carga en kilogramos.
  4. **Despacho Atómico & Hoja de Ruta del Conductor:** Descuento transaccional del inventario en base de datos al confirmar la salida y generación de manifiestos imprimibles para choferes con datos de contacto de comités comunitarios e instrucciones de cadena de frío.
  5. **Migración e Interoperabilidad Bidireccional con Excel:** Exportación consolidada en `.xlsx` con 3 pestañas dinámicas (Inventario FEFO, Alertas y Rutas) y zona drag-and-drop para carga masiva con validación y previsualización previa en navegador.

---

## Experiencia en Industria

### Aristor Consultoría — Analista de Datos (Prácticas Profesionales)
*Querétaro, México | Mayo 2025 – Septiembre 2025*

- Diseñé y programé una herramienta de análisis espacial basada en microdatos geoestadísticos del INEGI para la detección automatizada de zonas óptimas de expansión comercial en el sector de restaurantes y servicios.
- Estructuré el pipeline de ingesta, filtrado geoespacial y modelado predictivo para evaluar viabilidad de apertura de nuevos establecimientos.
- Facilité la toma de decisiones basada en datos para consultores y clientes finales mediante mapas de calor y scoring de potencial de mercado.

---

## Liderazgo & Startups

### AB-Tec — CEO & Co-Fundador
*Periodo: 2024 – 2025 (Pausado por compromisos académicos)*  
*Equipo: 5 estudiantes*

- Co-fundé y lideré como CEO una startup estudiantil enfocada en productos de higiene y cuidado personal.
- Diseñamos, formulamos y comercializamos geles antibacteriales con fórmula química propia.
- Gestioné la estrategia operativa, producción inicial, asignación de costos y ventas directas dentro de la comunidad universitaria.
- El proyecto se detuvo estratégicamente para priorizar la carga académica de alta exigencia de la doble titulación.

---

## Organizaciones Estudiantiles & Competiciones

### LEIA (Laboratorio Estudiantil de Inteligencia Artificial) — Co-Fundador & Líder Técnico
*Tecnológico de Monterrey, Campus Querétaro | 2024 – Presente*

#### 1. "From the Kitchen to the Cloud" — 13-Week Data Challenge (Databricks & Sun Holdings)
*Septiembre 2026 – Diciembre 2026 (En progreso)*
- Participación activa con equipo multidisciplinario de LEIA en el reto corporativo de 13 semanas impulsado por Databricks, Inc. y Sun Holdings.
- Enfoque técnico: Desarrollo de pipelines de datos masivos, modelos de Machine Learning y agentes de IA en Databricks sobre datos transaccionales multi-sucursal de cadenas como Applebee's (detección de fraude) o Taco Bueno (analítica de promociones y pricing).
- Certificación oficial de Databricks durante la Fase 1 (Semanas 1–4) y desarrollo con mentoría ejecutiva hacia el pitch final por el premio de $1,500 USD (Diciembre 2026).

#### 2. DAVE — Driver Attention & Vigilance Engine (Automotive Edge AI & IoT DMS)
- Co-creador del sistema integral de monitoreo de atención y fatiga del conductor (*Driver Monitoring System - DMS*) para cabina vehicular.
- **1er lugar en Expo Ingenierías** de Tec de Monterrey.
- Repositorio oficial: [LEIA-qro/Attention-Algorithm](https://github.com/LEIA-qro/Attention-Algorithm).
- Pipeline de visión artificial con MediaPipe Face Landmarker v2 (malla 3D de 478 puntos), métricas biomecánicas (EAR, MAR, head pose, mirada) y detección de distracciones con YOLOv8.
- Despliegue en Raspberry Pi 5 + acelerador Hailo-8 NPU alcanzando inferencia en tiempo real a **~30 FPS** con exportación de clips pre/post-incidente.
- Plataforma completa con API en FastAPI (Docker) y dashboard telemático para flotas en React + TypeScript + Vite + Tailwind CSS.

#### 3. Talleres Universitarios de Inteligencia Artificial
- Organización y docencia de 2 talleres teórico-prácticos sobre fundamentos de IA y Reinforcement Learning (Q-Learning y PPO) para más de 30 estudiantes universitarios por sesión.
