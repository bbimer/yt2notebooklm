# yt2notebooklm: Multi-Domain Research and Knowledge Extraction Engine

Autonomous transformation of heterogeneous technical sources (YouTube video transcripts, official web documentation, whitepapers, and academic publications) into verified, structured, multi-layer educational modules formatted for Google NotebookLM, Markdown knowledge bases, DOCX, and PDF.

---

## 1. System Overview and Core Invariants

The engine solves the problem of automated deep extraction of verified engineering and domain knowledge from noisy unstructured sources without human intervention and without token wastage.

### Core Architectural Invariants

1. **Isomorphic Ingestion Contract (`SourceContent`):**
   The two-pass analytical core (`analysis.py`), claim verifier (`verification.py`), and exporter (`publishing.py`) are strictly agnostic to source origin. Both YouTube video transcripts (timestamped) and web pages / documentation (sectioned via `[SEC-XX]`) normalize into the unified `SourceContent` data model.

2. **Strict Two-Pass AI Evaluation (Gatekeeper -> Methodist):**
   - **Pass A (Gatekeeper):** Fast, low-cost evaluation of relevance, technical depth, and commercial noise. Rejects marketing fluff, affiliate promotions, and superficial summaries. When rejected, Pass B is skipped to prevent token waste.
   - **Pass B (Methodist):** Executes only on accepted sources. Deconstructs the source into 4 distinct knowledge layers: Market/Engineering Mechanics, Verified Facts vs Opinions with anchors, Pitfalls/Myths, and Practical Implementation.

3. **Multi-Domain Architecture:**
   Knowledge is partitioned by domain profiles located in `config/domains/<domain>.yaml` and stored in `knowledge_base/domains/<domain>/`. Supported domains include:
   - `crypto_trading`: Market microstructure, delta-neutral arbitrage, order routing, funding.
   - `computer_science`: Numeral systems, ALU hardware arithmetic, CPU architecture, standards (IEEE 754).
   - Custom extensible domains via configuration.

4. **Claim Verification & Strict Non-Hallucination:**
   Author assertions are verified against domain ground truth (`PRODUCT_CLAIMS.md` or domain references). Unsubstantiated claims are marked as hypotheses and prevented from entering production sales or engineering playbooks.

5. **Multi-Format Publication Pipeline:**
   Export targets include:
   - Google NotebookLM discrete knowledge packs (`exports/notebooklm_pack/`).
   - Single-file master bundles (`exports/notebooklm_bundle.md`).
   - Structured CSV indexes (`exports/index.csv`).
   - Production academic PDFs and Word documents conforming to official standards (via Pandoc, KaTeX, and Playwright).

6. **Pure Knowledge Base on Disk (Option A) & In-Memory Prompt Injection:**
   Files saved to `digests/*.md` contain exclusively clean metadata, author chapters/timestamps, and paragraph-split transcripts with zero embedded prompt boilerplate. This ensures 100% clean ingestion into Google NotebookLM, Claude Projects, and RAG vector databases without vector contamination or Audio Overview prompt leakage. Ready-to-execute prompts are attached strictly in-memory into the clipboard on demand.

7. **Multi-Source Comparative Synthesis (`prompt compare`):**
   Specialized prompts for analyzing 2+ video transcripts simultaneously: extracting consensus, highlighting technical and ideological disputes, fact-checking author claims against one another, extracting unique per-source gems, and generating a unified synthesis matrix without redundancies.

8. **OS-Level Keyboard Integration (`whkd` + `komorebi`):**
   Seamless integration with Windows tiling window managers via `whkd`, offering zero-latency global hotkeys for background downloading, clipboard path copying (without trailing `\r\n`), prompt generation, and audio confirmation chimes.

---

## 2. Agent Execution Guide: Operating Instructions for AI Agents

This section is a machine-readable protocol for autonomous agents operating inside or with this repository.

### Quick Orientation for Agents

- **Root CLI Command:** `research` (entry point defined in `pyproject.toml` pointing to `research_academy.cli:cli` or `python -m research_academy.cli`).
- **Configuration Root:** `config/` (contains `scoring.yaml`, `topics.yaml`, `schedule.yaml`, `domains/`).
- **Database:** SQLite at `data/research_academy.db` managed via `research_academy.database:Database`.
- **Primary Code Modules:** `src/research_academy/`.
- **Knowledge Base Output:** `knowledge_base/domains/<domain>/sources/<topic>/` and `digests/`.
- **Test Suite:** 65 pytest cases covering all providers, pipelines, models, CLI tools, and hotkey workflows.

### Agent Workflow Playbooks

#### Playbook A: Ingest and Analyze a Web Page or Documentation URL
When tasked with extracting knowledge from an article, documentation page, or technical blog:
```bash
# 1. Fetch, decompile into clean markdown, split into [SEC-XX], and run 2-pass analysis
research web ingest "https://example.com/article" --domain computer_science --topic 01_binary_numeral_system --analyze

# 2. View database record and ingestion status
research status
```

#### Playbook B: Ingest and Analyze a YouTube Video
When given a YouTube URL or video ID:
```bash
# Process video through transcript extraction, Gatekeeper Pass A, and Methodist Pass B
research process --video-id "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### Playbook C: Ad-Hoc Video Digest and In-Memory Prompt Extraction
When extracting a single video transcript into a clean knowledge-base file with ready-to-execute prompt copied to clipboard:
```bash
# Ingest single URL and copy Summary prompt payload into clipboard
research digest "https://www.youtube.com/watch?v=6BW4lo7f71I" --mode summary

# Process video from clipboard URL and copy Audit prompt payload
research digest --from-clipboard --mode audit
```

#### Playbook D: Re-Using Saved Digests (In-Memory Wrapping without Disk Modification)
When retrieving the latest digest or re-wrapping an older file with a new prompt mode:
```bash
# Copy clean absolute file path to clipboard (no \r\n, ready for browser Ctrl + O)
research latest-digest

# In-memory wrap latest digest with Critical Audit prompt and copy to clipboard
research latest-digest -m audit

# In-memory wrap older digest from last week with Tutorial prompt
research latest-digest -f "digests/2026-10-31_sample.md" -m tutorial

# Reveal file in Windows Explorer or open in editor
research latest-digest --reveal
research latest-digest --open
```

#### Playbook E: Standalone Prompts for Attached Files (`Ctrl + O` Workflow)
When files are already attached in Claude, ChatGPT, or NotebookLM via file upload (`Ctrl + O`), avoid duplicate transcript text in the chat input box by copying standalone prompts:
```bash
# Copy Executive Summary prompt for 1 attached file
research prompt summary

# Copy Critical Audit (Bullshit & Scam Filter) prompt for 1 attached file
research prompt audit

# Copy Actionable Tutorial prompt for 1 attached file
research prompt tutorial

# Copy Multi-Source Comparison & Synthesis prompt for 2+ attached files
research prompt compare
```

#### Playbook F: Automated Matrix Harvesting
To scan configured query matrices, filter negative keywords, and extract top candidate videos:
```bash
research harvest --topic 01_market_structure
```

#### Playbook G: Compiling Knowledge Bundles and Academic Reports
To generate structured knowledge bundles or format academic reports after ingestion:
```bash
# Generate NotebookLM pack (day-based discrete modules)
research export --format notebooklm

# Generate unified single bundle
research export --format bundle

# Generate tabular CSV index
research export --format csv

# Render vector PDF with KaTeX math, dot leaders, and symmetric 20mm margins
python scratch/build_perfect_pdf.py

# Export to Word DOCX with native OMML mathematical formulas
pandoc -f markdown+pipe_tables knowledge_base/domains/computer_science/referat_binary_numeral_systems_ua.md -o knowledge_base/domains/computer_science/referat_binary_numeral_systems.docx
```

#### Playbook H: Running Diagnostic Checks
Before initiating operations, verify environment integrity:
```bash
research doctor
```

---

## 3. Global Desktop Hotkeys (`whkd` + `komorebi`)

The system integrates directly with Windows hotkey daemon (`whkd`) and the HUD overlay (`cheatsheet.py`):

| Hotkey | Action | Workflow Context |
| :--- | :--- | :--- |
| **`Alt + D`** | Ingest YouTube URL from clipboard & copy **Summary** payload | Immediate video processing from browser link |
| **`Alt + Shift + D`** | Ingest YouTube URL from clipboard & copy **Audit** payload | Scam/fluff detection on newly found video |
| **`Alt + Ctrl + D`** | Copy clean path to latest digest (without `\r\n`) | Press before `Ctrl + O` in browser upload dialog |
| **`Alt + Ctrl + S`** | Copy standalone **Summary** prompt | Paste into chat after attaching 1 `.md` file |
| **`Alt + Ctrl + A`** | Copy standalone **Audit** prompt | Paste into chat after attaching 1 `.md` file |
| **`Alt + Ctrl + C`** | Copy **Multi-Source Compare & Synthesis** prompt | Paste into chat after attaching **2+ `.md` files** |
| **`Alt + Ctrl + E`** | Reveal latest digest in Windows Explorer | Direct folder access to generated files |
| **`Alt + Ctrl + O`** | Open latest digest in VS Code / default editor | Manual review and editing |
| **`Alt + O`** | Reload `whkd` daemon | Apply hotkey configuration updates |
| **`Alt + /` / `Alt + F1`** | Show GUI Hotkey Cheat-Sheet HUD | On-screen interactive hotkey reference |

---

## 4. Project Directory Structure

```
nullspread-research-academy/
├── README.md                          # Engine documentation and agent manual
├── pyproject.toml                     # Python packaging and dependency specs
├── .env.example                       # Environment variable templates
├── config/                            # Pipeline and domain configurations
│   ├── scoring.yaml                   # Thresholds, scoring weights, stop-words
│   ├── topics.yaml                    # Query matrices and topic definitions
│   ├── trusted_channels.yaml          # Institutional whitelist channels
│   ├── schedule.yaml                  # Background scheduling configuration
│   └── domains/                       # Domain profile configurations
│       ├── crypto_trading.yaml        # Market microstructure domain
│       └── computer_science.yaml      # Architecture & algorithms domain
├── digests/                           # Pure knowledge-base digests (Option A)
│   └── YYYY-MM-DD_<id>_<slug>.md     # Title, Passport, Chapters, Paragraph Transcripts
├── src/
│   └── research_academy/
│       ├── cli.py                     # Click CLI interface (digest, prompt, latest-digest)
│       ├── config.py                  # Pydantic v2 application configuration
│       ├── database.py                # SQLite repository, schema, and queries
│       ├── models.py                  # Domain models (SourceContent, Passes, Reviews)
│       ├── scheduler.py               # Background task scheduler
│       ├── providers/
│       │   ├── base.py                # Abstract provider contracts
│       │   ├── youtube_api.py         # YouTube Data API v3 provider
│       │   ├── yt_dlp_provider.py     # yt-dlp fallback discovery
│       │   ├── transcripts.py         # Transcript extraction engine
│       │   ├── audio_fallback.py      # Groq Whisper fallback provider
│       │   └── mock_provider.py       # Deterministic test provider
│       ├── pipeline/
│       │   ├── ad_hoc_digest.py       # Ad-hoc digest engine & in-memory prompt builder
│       │   ├── closer_fast_track.py   # Institutional sales playbook generator
│       │   ├── discovery.py           # Candidate discovery coordinator
│       │   ├── deduplication.py       # URL / Video ID deduplication
│       │   ├── ranking.py             # Pre-LLM mathematical heuristics
│       │   ├── normalization.py       # Domain terminology transcript normalizer
│       │   ├── transcription.py       # Transcript acquisition flow
│       │   ├── web_extractor.py       # Web source parser & decompiler
│       │   ├── sampling.py            # Segment-based transcript window sampler
│       │   ├── analysis.py            # Two-pass LLM pipeline (Gatekeeper + Methodist)
│       │   ├── verification.py        # Fact and boundary verification against ground truth
│       │   └── publishing.py          # Exporter to Markdown, CSV, and NotebookLM packs
│       ├── llm/
│       │   ├── base.py                # Abstract LLM provider interface
│       │   ├── gemini.py              # Google Gemini implementation
│       │   ├── openrouter.py          # OpenRouter multi-model LLM provider
│       │   ├── mock_llm.py            # Deterministic Mock LLM for offline tests
│       │   └── prompts.py             # Prompts for Gatekeeper, Methodist, and Verifier
│       └── academy/
│           ├── question_generator.py  # Managerial test questions generator
│           ├── evaluation.py          # Strict evaluation & critical error blocker
│           └── roleplay.py            # Interactive client simulation sparring
├── knowledge_base/                    # Persistent curated knowledge repository
│   ├── product/                       # Ground truth claims (PRODUCT_CLAIMS.md)
│   └── domains/                       # Domain-partitioned knowledge bases
│       ├── crypto_trading/            # Crypto trading sources and modules
│       └── computer_science/          # CS sources, DOCX, and academic PDF reports
├── exports/                           # Staging directory for generated bundles
│   └── notebooklm_pack/               # Discrete daily modules, battlecards, and playbooks
├── data/                              # SQLite persistent storage (research_academy.db)
└── tests/                             # 65 unit and integration pytest suites
```

---

## 5. CLI Reference Manual

| Command | Arguments / Flags | Description |
| :--- | :--- | :--- |
| `research digest` | `<url_or_id> [--mode summary\|audit\|tutorial]` | Ingest single video, save clean `.md` to `digests/`, and copy payload to clipboard. |
| `research digest` | `--from-clipboard [--mode ...]` | Ingest YouTube URL directly from clipboard. |
| `research latest-digest` | `[-m summary\|audit\|tutorial\|compare] [-f <file>] [-c/-nc] [-o] [-r]` | Copy clean path to clipboard (default) or in-memory wrap content with selected prompt. |
| `research prompt` | `[summary\|audit\|tutorial\|compare] [-m ...]` | Copy standalone prompt for attached files into clipboard. |
| `research doctor` | None | Validates database connectivity, API key presence, directory structure, and dependencies. |
| `research status` | None | Displays database record counts, pipeline breakdown by status (PENDING, ACCEPT, REJECT, PROCESSED). |
| `research domain list` | None | Lists all registered knowledge domains and their configured root directories. |
| `research domain info` | `<name>` | Outputs topics, target keywords, and scoring weights for a specified domain. |
| `research web search` | `--topic <name> [--domain <name>]` | Discovers primary web articles, documentation pages, and RFCs for a topic. |
| `research web ingest` | `<url> [--domain <name>] [--topic <name>] [--analyze/--no-analyze]` | Fetches web article, decomposes into `[SEC-XX]` segments, and runs 2-pass analysis. |
| `research search` | `--topic <name>` | Queries YouTube for candidate videos according to configured search matrices. |
| `research process` | `--video-id <url_or_id>` | Runs transcript extraction, Gatekeeper Pass A, and Methodist Pass B on a video. |
| `research harvest` | `--topic <name>` | Autonomous matrix harvester: discovers candidates, filters stop words, and processes transcripts. |
| `research audit` | `<url_or_id>` | Instant subtitle extraction and 5-point audit prompt copied directly to clipboard. |
| `research sniffer` | None | Clipboard daemon: intercept YouTube links copied in browser and generate audit prompts. |
| `research update` | `[--dry-run]` | Executes the full automated update cycle (discovery -> ingest -> analyze -> export). |
| `research retry-failed` | None | Retries failed transcript fetches using alternate providers or Whisper fallback. |
| `research export` | `--format <notebooklm\|bundle\|csv\|markdown>` | Compiles curated intelligence into requested delivery formats. |
| `research academy quiz` | `--topic <name>` | Launches technical quiz based on verified source knowledge. |
| `research academy roleplay` | `[--difficulty easy\|medium\|hard]` | Interactive sparring session with simulated skeptical institutional client. |

---

## 6. Setup and Verification

### Prerequisites
- Python 3.12 or higher.
- Git.
- Optional: Google Chrome or Microsoft Edge (for Playwright PDF rendering).
- Optional: Pandoc 3.0+ (for DOCX export).

### Installation
```bash
git clone https://github.com/bbimer/yt2notebooklm.git
cd yt2notebooklm
pip install -e .
```

### Environment Configuration
Copy `.env.example` to `.env` and provide required keys:
```env
# Primary LLM Options (at least one required for live LLM execution)
OPENROUTER_API_KEY=your_openrouter_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# YouTube Discovery (optional; mock provider activates if absent)
YOUTUBE_API_KEY=your_youtube_data_api_v3_key_here

# Audio Fallback (optional)
GROQ_API_KEY=your_groq_whisper_key_here
```

### Verification
Run the complete 65-test test suite to ensure all subsystems, models, pipelines, and hotkey generators operate within parameters:
```bash
pytest
```
All tests use deterministic mocks and run offline without consuming live API quotas or leaking secrets.
