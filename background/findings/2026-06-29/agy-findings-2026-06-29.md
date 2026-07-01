# Diego Perea - Personal & Technical Profile Findings

This file compiles factual findings about the user (Diego Perea) based on historical conversation databases retrieved from the system.

---

## 1. Personal Details
* **Name**: Diego Perea (derived from database user folder paths `C:\Users\Diego Perea`).
* **Location**: No Findings
* **Profession**: University Student.
  * *Evidence/Citation*: Project directories include paths like `Cuarto Semestre` (4th Semester) and class names like `Criptografía` (Cryptography), indicating he is in his 4th semester of a university program (likely Computer Science or Software Engineering).
* **Interests**: 
  * **Game Development**: Game design, labyrinth mechanics, and rendering using Raylib in C#.
  * **Reinforcement Learning**: Implementing, training, and optimizing reinforcement learning agents (PPO, SAC) in emulation environments (BizHawk).
  * **Edge AI & Computer Vision**: Working with hardware accelerators (Hailo-8) on single-board computers (Raspberry Pi 5) for surveillance applications.
  * **Cryptography**: Hash functions, collision search algorithms, and birthday attacks.
* **Preferences**: Highly structured workflows, strict adherence to defined processes (such as superpower skills), and thorough validation before marking tasks complete.

---

## 2. Communication Style
* **Information Structure**: Prefers organized, concise, and structured delivery. Uses bullet points, markdown code listings, and clear headings.
* **Tone**: Professional, direct, task-oriented, and objective. Encourages independent verification rather than performative agreement.
* **Formatting Habits**:
  * Frequently uses clear GitHub-style alerts (`[!NOTE]`, `[!IMPORTANT]`, `[!WARNING]`) in implementation plans.
  * Links files using standard markdown notation with the `file://` scheme (e.g., `[filename](file:///path/to/file)`).
  * Prefers English for direct agent instructions, while using Spanish for academic work, class projects, and local environment files (e.g., `Cuarto Semestre`, `Criptografía`).

---

## 3. Goals & Projects

* **Ongoing/Past Projects**:
  1. **Labyrinth Game (`labrynth_Game`)**: A C# game using Raylib. Features a dungeon engine utilizing memory chain history queues (`Queue<LabyrinthNode>`), pathfinding/labyrinth generation, camera controller (`CameraController.cs`), and entity states (enemies, loot, doors). Located under `Documents\Created Games\raw\labrynth_Game`.
  2. **Attention-Algorithm / Surveillance System**: An object-detection camera surveillance system built for the Raspberry Pi 5 with a Hailo-8 AI accelerator. Features custom frame ring-buffering, pre/post-trigger recording windows, and custom video clip writing (`CustomClipWriter`). Located under `Documents\Code\Attention-Algorithm`.
  3. **Street Fighter RL Engine**: Reinforcement learning environment wrapping the BizHawk emulator (v2.8). Uses SAC and PPO agents tuned with Optuna (`optuna_study.py`), Lua interface scripts (`training_env_client.lua`, `generated_config.lua`), and custom observation normalization. Located under `Documents\Apps\BizHawk-2.8-win-x64\street_fighter`.
  4. **Cryptography Birthday Attack**: An interactive Python console program (`hash_rainbowT_bdattack.py` and `tests/test_cryptography.py`) for a cryptography course. Performs lookups on precomputed tables and birthday attacks to find collisions in a truncated SHA-256 hash function (`MySHA6`). Located under `Documents\Code\Cuarto Semestre\Criptografía`.

---

## 4. Technical Context
* **Programming Languages**:
  * **Python**: Primary language for machine learning, reinforcement learning, and math/cryptography scripts.
  * **C#**: Primary language for game logic, Raylib bindings, and dotnet unit tests.
  * **Lua**: Used for emulator scripting (BizHawk game state monitoring).
  * **LaTeX**: Used for university reports and typesetting.
* **Tools, Libraries & Frameworks**:
  * **Testing**: `pytest` (Python), `dotnet test` (C#).
  * **AI/CV**: `cv2` (OpenCV), `PyTorch` (implied by RL agents PPO/SAC), Hailo-8 SDK.
  * **Emulation & UI**: BizHawk Emulator (v2.8), Raylib.
  * **Environments**: Windows OS, PowerShell, Python Virtual Environments (`.venv`).
* **Skill Level & Domain Expertise**: Advanced. Demonstrated experience with custom data structures (frame ring buffers), math-heavy algorithms (cryptography attacks), emulator hooking (Lua memory injection), hyperparameter optimization (Optuna), and machine learning (SAC/PPO policies).


