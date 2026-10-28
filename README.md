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

---

## 2. Agent Execution Guide: Operating Instructions for AI Agents

This section is a machine-readable protocol for autonomous agents operating inside or with this repository.

### Quick Orientation for Agents

- **Root CLI Command:** `research` (entry point defined in `pyproject.toml` pointing to `research_academy.cli:cli`).
- **Configuration Root:** `config/` (contains `scoring.yaml`, `topics.yaml`, `schedule.yaml`, `domains/`).
- **Database:** SQLite at `data/research_academy.db` managed via `research_academy.database:Database`.
- **Primary Code Modules:** `src/research_academy/`.
- **Knowledge Base Output:** `knowledge_base/domains/<domain>/sources/<topic>/`.
- **Test Suite:** 52 pytest cases covering all providers, pipelines, models, and CLI tools.

### Agent Workflow Playbooks

#### Playbook A: Ingest and Analyze a Web Page or Documentation URL
When tasked with extracting knowledge from an article, documentation page, or technical blog:
```bash
# 1. Fetch, decompile into clean markdown, split into [SEC-XX], and run 2-pass analysis
research web ingest "https://example.com/article" --domain computer_science --topic 01_binary_numeral_system --analyze

# 2. View database record and ingestion status
research status
```
Programmatic equivalent:
```python
from research_academy.pipeline.web_extractor import WebExtractor
from research_academy.pipeline.analysis import AnalysisPipeline
from research_academy.config import AppConfig

config = AppConfig.load()
extractor = WebExtractor()
source_content = extractor.extract_from_url("https://example.com/article", domain="computer_science", topic="01_binary_numeral_system")
# source_content.segments contain [SEC-01], [SEC-02] anchors
```

#### Playbook B: Ingest and Analyze a YouTube Video
When given a YouTube URL or video ID:
```bash
# Process video through transcript extraction, Gatekeeper Pass A, and Methodist Pass B
research process --video-id "https://www.youtube.com/watch?v=VIDEO_ID"
```
Programmatic equivalent:
```python
from research_academy.pipeline.transcription import TranscriptPipeline
from research_academy.pipeline.analysis import AnalysisPipeline
# Subtitles are fetched without audio transcription in 95% of cases via youtube-transcript-api.
```

#### Playbook C: Automated Matrix Harvesting
To scan configured query matrices, filter negative keywords, and extract top candidate videos:
```bash
research harvest --topic 01_market_structure
```

#### Playbook D: Compiling Exports for NotebookLM
To generate fresh knowledge bundles after ingestion:
```bash
# Generate NotebookLM pack (day-based discrete modules)
research export --format notebooklm

# Generate unified single bundle
research export --format bundle

# Generate tabular CSV index
research export --format csv
```

#### Playbook E: Running Diagnostic Checks
Before initiating operations, verify environment integrity:
```bash
research doctor
```

---

## 3. Project Directory Structure

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
├── src/
│   └── research_academy/
│       ├── cli.py                     # Click CLI interface
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
├── data/                              # SQLite persistent storage (research_academy.db)
└── tests/                             # 52 unit and integration pytest suites
```

---

## 4. CLI Reference Manual

| Command | Arguments / Flags | Description |
| :--- | :--- | :--- |
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

## 5. Data Contracts and Pipeline Mechanics

### Unified `SourceContent` Model
Defined in `src/research_academy/models.py`:
```python
class SourceSegment(BaseModel):
    segment_id: str          # "00:01:23" for video or "[SEC-01]" for web
    start_sec: float         # Starting second or sequential ordinal
    end_sec: float           # Ending second or sequential ordinal
    text: str                # Normalized content text

class SourceContent(BaseModel):
    source_id: str           # YouTube video_id or SHA256 web slug
    source_type: str         # "youtube" | "web"
    title: str               # Document or video title
    url: str                 # Canonical source URL
    domain: str              # Target domain (e.g. "computer_science")
    topic: str               # Topic identifier
    segments: list[SourceSegment]
    raw_markdown: str = ""   # Full preserved markdown body
```

### Gatekeeper Pass A Result Contract
```python
class GatekeeperPassAResult(BaseModel):
    decision: GatekeeperDecision  # ACCEPT (>=7.0) | REVIEW (5.5-6.9) | REJECT (<5.5)
    relevance_score: float        # 1.0 - 10.0
    technical_depth_score: float  # 1.0 - 10.0
    practical_value_score: float  # 1.0 - 10.0
    source_quality_score: float   # 1.0 - 10.0
    commercial_noise_score: float # 1.0 - 10.0 (penalty)
    reasoning: str
```

### Methodist Pass B Result Contract
```python
class MethodistPassBResult(BaseModel):
    summary: str
    key_takeaways: list[str]
    technical_mechanisms: list[str]
    claims_analysis: list[ClaimItem]      # Claims matched with [SEC-XX] or timestamps
    applied_rules: list[str]
    client_questions: list[ClientQnA]     # 5 tough client questions with model answers
    industry_slang: list[SlangTerm]
    confidence_score: float
```

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
Run the complete 52-test test suite to ensure all subsystems, models, and pipelines operate within parameters:
```bash
pytest
```
All tests use deterministic mocks and run offline without consuming live API quotas or leaking secrets.
