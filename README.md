# EDXSO Automated Micro-Influencer Outreach System

An automated end-to-end intelligence and outreach pipeline designed to discover, qualify, enrich, and contact Tech & AI micro-influencers. Built with a focus on audit transparency, zero-hallucination contact enrichment, guardrailed LLM personalization, and idempotent dispatch safety.

---

## 1. System Architecture & Pipeline Flow

The platform operates as a multi-stage sequential pipeline where every stage produces verifiable data contracts:

```text
┌────────────────────────┐
│  Influencer Discovery  │ ──► YouTube Data API v3 (Search query rotation + 50-item batching)
└───────────┬────────────┘
            │
┌───────────▼────────────┐
│ Multi-Metric Audit Log │ ──► Threshold Evaluation (5k-100k subs, engagement >= 0.05%, Tech/AI)
└───────────┬────────────┘     (Pass: Qualified | Fail: Retained with transparent Audit Reason)
            │
┌───────────▼────────────┐
│   Profile Enrichment   │ ──► Strict Regex Email Extraction (Zero-hallucination "Not Found" fallback)
└───────────┬────────────┘     + Recent Video Metadata extraction (titles, themes, tags)
            │
┌───────────▼────────────┐
│   AI Personalization   │ ──► Gemini 2.5 Flash + Programmatic Guardrail Loop
└───────────┬────────────┘     • Email: 60–90 words, executive tone, contextual hook
            │                  • Instagram DM: 15–30 words, punchy, conversational
┌───────────▼────────────┐
│ Sending & State Safety │ ──► Dual-Mode Dispatcher (Safe Simulation vs Live SMTP)
└───────────┬────────────┘     + Idempotent Hash State Machine (Duplicate spam prevention)
            │
┌───────────▼────────────┐
│  Outreach Tracker CSV  │ ──► Permanent Audit Log (`SENT`, `SIMULATED`, `SKIPPED_DUPLICATE`)
└────────────────────────┘
```

---

## 2. Engineering Decisions & Thought Process

During the architectural design and implementation, several core technical trade-offs were evaluated:

### Q1: Why retain non-qualified creators instead of silently discarding them?
* **Initial Thought:** Filter out anyone outside the 5,000–100,000 follower range immediately to keep the database compact.
* **Senior Decision:** Discarding failed records creates a black-box system where marketers and evaluators cannot verify whether a creator was missed or intentionally disqualified. We implemented a full **Audit Trail** classification:
  * Macro creators like *Programming with Mosh* (5.18M) and *Internet Made Coder* (362k) are classified with `FAILED_FOLLOWER_COUNT (Above 100k limit)`.
  * Nano creators (<5k) are tagged with `FAILED_FOLLOWER_COUNT (Below 5k limit)`.
  * Inactive creators are tagged with `FAILED_ENGAGEMENT_RATE`.
  This preserves complete transparency across all 55 discovered channels.

### Q2: What is the policy for missing creator emails?
* **Initial Thought:** Use an LLM to predict or search external web patterns to guess emails.
* **Senior Decision:** Strict **Zero Hallucination Policy**. Scraping or inventing emails damages domain deliverability and violates privacy trust. If a creator's public metadata (channel description, video descriptions) does not contain a verified regex email pattern, the system marks them explicitly as `"Not Found"` and categorizes their outreach state as `SKIPPED_NO_EMAIL`. These creators are cleanly redirected to the **Instagram DM Workflow Queue**.

### Q3: Why separate Email and Instagram DM into distinct workflows?
* **Initial Thought:** Automate both Email and Instagram DMs via direct API endpoints.
* **Senior Decision:** Meta's Graph API strictly restricts automated private messages without manual app review and partner authorization; third-party scraping scripts frequently trigger account shadowbans. To maintain enterprise compliance, the system uses a **Dual-Channel Strategy**:
  1. **Email:** Fully automated dispatch (with Simulation Mode safety toggle).
  2. **Instagram DM:** Assisted manual queue. The UI generates compliant 15–30 word DMs, links directly to the creator's verified Instagram handle, and provides a one-click copy/open workflow.

### Q4: How do we prevent email spam if a user clicks Dispatch multiple times?
* **Initial Thought:** Just append every send event to a CSV log.
* **Senior Decision:** Outreach tools must be **Idempotent**. If an operator presses "Execute Outreach" five times, the system must not spam creators five times. The dispatcher cross-references the creator's unique channel ID and email against previous successful dispatches. Subsequent runs cleanly transition the status to `SKIPPED_DUPLICATE` without re-firing network requests.

### Q5: How do we guarantee LLM messages adhere strictly to 60–90 words without fluff?
* **Initial Thought:** Rely solely on prompt instructions like *"write between 60 to 90 words"*.
* **Senior Decision:** LLMs are notoriously loose with token-to-word counts. We implemented a **Two-Tier Personalization Guardrail**:
  1. *Prompt-Level Instruction:* Structural constraints forbidding buzzwords, pleasantries ("Hope you are having a wonderful day!"), and robotic templates.
  2. *Programmatic Validation Loop:* A post-generation word-counter checks if `len(words) < 60` or `len(words) > 90`. If violated, a targeted self-correction refinement prompt executes automatically before storing the message.

### Q6: How does the discovery engine scale from 50 to 500+ creators efficiently?
* **Initial Thought:** Make separate single-channel search queries one by one.
* **Senior Decision:** YouTube v3 quota limits search operations to 100 units per search call. Scaling to 500+ creators requires:
  1. **Cursor-based pagination (`nextPageToken`):** Traversing YouTube API result pages deterministically without duplicate fetches.
  2. **Sub-niche query rotation:** Rotating search vectors (e.g., `"machine learning tutorial"`, `"pytorch developer"`, `"llm engineering"`, `"python ai tools"`) to discover non-overlapping creator cohorts.
  3. **ID Batching:** Batching up to 50 channel IDs into a single `channels.list(id=..., part='statistics,snippet')` endpoint call, consuming only 1 quota unit for 50 creators instead of 50 units.

---

## 3. Deliverables Summary

| Deliverable | Location | Description |
| :--- | :--- | :--- |
| **Deliverable A: Interactive UI** | `app.py` | Modern Streamlit dashboard (`localhost:8501`) featuring Discovery Pool, Audit Table, AI Studio, and Dispatch Tracker. |
| **Deliverable B: Influencer Dataset** | `data/influencer_dataset.csv` | 55 real creators with Followers, Engagement Rate, Niche, Email, Content Themes, Status, and Audit Reason. |
| **Deliverable C: Personalized Pitches** | `data/personalized_messages.json` | Guardrailed Email pitches (60–90 words) and Instagram DMs (15–30 words) referencing recent video content. |
| **Deliverable D: Outreach Tracker** | `data/outreach_tracker.csv` | Full delivery state tracking (`SENT`, `SIMULATED`, `SKIPPED_DUPLICATE`, `SKIPPED_NO_EMAIL`). |
| **Deliverable E: Architecture & Docs** | `README.md` | Comprehensive system design, operational guides, and decision records. |

---

## 4. Tech Stack

* **Core Language:** Python 3.9+
* **Data Ingestion:** YouTube Data API v3 (`google-api-python-client`, `requests`)
* **AI Personalization:** Google Gemini 2.5 Flash API
* **Data Engineering & Models:** Pandas, Pydantic v2
* **Web UI Dashboard:** Streamlit with custom slate design system
* **Security & Configuration:** `python-dotenv`, `certifi`

---

## 5. Local Setup & Execution Guide

### Prerequisites
* Python 3.9 or higher installed
* Valid Google YouTube Data API Key
* Valid Google Gemini API Key

### Step 1: Clone the repository
```bash
git clone https://github.com/sanskritig007/micro-influencer-outreach.git
cd micro-influencer-outreach
```

### Step 2: Set up virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Create a `.env` file in the project root:
```env
YOUTUBE_API_KEY=your_youtube_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Real SMTP email delivery (if Simulation Mode is turned off)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Step 4: Run the Web Dashboard
```bash
streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.

---

## 6. Directory Structure

```text
micro-influencer-outreach/
├── data/
│   ├── raw_influencers.json       # Raw YouTube extraction pool (55 creators)
│   ├── filtered_influencers.json  # Qualified creators meeting criteria
│   ├── influencer_dataset.csv     # Deliverable B: Complete dataset with audit reasons
│   ├── personalized_messages.json # Deliverable C: Guardrailed Email & IG DM pitches
│   └── outreach_tracker.csv       # Deliverable D: Real-time execution log
├── src/
│   ├── config.py                  # Threshold constants (5k-100k, 0.05% engagement)
│   ├── models.py                  # Pydantic schemas (Creator, AuditStatus, Pitch)
│   ├── discovery/
│   │   └── youtube_fetcher.py     # YouTube API client with batching & metrics
│   ├── filtering/
│   │   └── classifier.py          # Multi-criteria audit classification engine
│   ├── enrichment/
│   │   └── contact_extractor.py   # Regex email extractor & profile enricher
│   ├── personalization/
│   │   ├── prompts.py             # Prompt engineering templates with word budgets
│   │   └── generator.py           # Gemini generation with self-correction guardrails
│   └── sending/
│       ├── dispatcher.py          # Dual-mode execution (Simulation / SMTP)
│       └── tracker.py             # Idempotency and CSV state tracker
├── app.py                         # Modern 4-tab Streamlit web application
├── requirements.txt               # Locked project dependencies
└── README.md                      # Deliverable E: Documentation & Architecture
```

---

## 7. Known Limitations & Production Roadmap

1. **YouTube API Quota:** The standard free-tier quota is 10,000 units/day. While batching optimizes this significantly (50 channels per read unit), scaling beyond 5,000 creators/day requires requesting an elevated quota from Google Cloud Console.
2. **Contact Email Accessibility:** YouTube's native "View Email Address" reCAPTCHA button cannot and should not be programmatically bypassed. The system extracts publicly declared business emails from video and channel descriptions. For production growth, integrating secondary B2B enrichment APIs (e.g., Hunter.io or Apollo) provides an additional verified data layer.
3. **Instagram Automation Restrictions:** Due to Meta's strict anti-spam guidelines, automated headless DMing risks profile penalties. The assisted queue workflow provides the optimal balance between operator productivity and platform compliance.
