# Automated Micro-Influencer Outreach System

An automated end-to-end pipeline that discovers relevant Tech & AI micro-influencers, qualifies them using multi-metric filtering, enriches their profiles with engagement and contact details, generates personalized pitches using LLMs, and manages dispatch tracking.

---

## Architecture & Workflow

```text
Discovery (YouTube API)
   │
   ▼
Channel Data Batching & Metrics Extraction
   │
   ▼
Multi-Factor Filtering & Classification (Followers 5k-100k, Engagement Rate, Niche)
   │
   ▼
Profile Enrichment (Email extraction, Content themes, Recent video context)
   │
   ▼
AI Personalization (Targeted Email pitch 60-90 words + Instagram DM 15-30 words)
   │
   ▼
Sending Layer (Dual-mode: Simulation / Live SMTP with Deduplication)
   │
   ▼
Outreach Tracker & CSV Logs
```

---

## Tech Stack

* **Language:** Python 3.9+
* **Data Extraction:** YouTube Data API v3 (batching optimized)
* **Data Modeling:** Pydantic v2
* **AI / LLM:** Google Gemini API
* **Data Processing:** Pandas
* **UI Dashboard:** Streamlit

---

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sanskritig007/micro-influencer-outreach.git
   cd micro-influencer-outreach
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Add your `YOUTUBE_API_KEY` and `GEMINI_API_KEY` in `.env`.

---

## Project Structure

```text
micro-influencer-outreach/
├── data/                      # Raw datasets, filtered outputs, outreach logs
├── src/
│   ├── config.py              # Configuration and threshold definitions
│   ├── models.py              # Pydantic data schemas
│   ├── discovery/             # YouTube API channel discovery & extraction
│   ├── filtering/             # Qualification and scoring logic
│   ├── enrichment/            # Email extraction and profile enrichment
│   ├── personalization/       # LLM personalized pitch generators
│   └── sending/               # Dispatch engine and outreach tracker
├── app.py                     # Streamlit dashboard
├── requirements.txt
└── README.md
```
