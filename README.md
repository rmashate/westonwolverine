# Weston Wolverine Brief

The **Weston Wolverine Brief** is a hyper‑local news digest for Weston and Mount Dennis (Toronto).  It automatically collects open data on crime, development and civic issues and delivers a concise weekly summary via email and SMS.  This repository contains the Python scrapers, digest generator, and a simple landing page for collecting subscribers.

## Project structure

```
westonwolverine/
├── README.md                – this file
├── requirements.txt         – Python package requirements
├── .env.example             – template for environment variables
├── scraper.py               – collects data from open sources
├── generate_digest.py       – composes a weekly digest from scraped data
├── send_digest.py           – emails the digest to subscribers
├── templates/
│   └── weekly_digest.md.j2  – Jinja2 template for the digest
├── landing/
│   └── index.html           – simple marketing page for pre‑launch sign‑ups
└── .github/
    └── workflows/
        └── run.yml         – GitHub Actions workflow (runs weekly)
```

## Installation

1. Clone or download this repository.
2. Copy `.env.example` to `.env` and populate your Supabase, Stripe and Brevo keys.  The Python scripts will automatically load this file if present.
3. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

4. Run the scraper to collect new data:

   ```sh
   python scraper.py
   ```

5. Generate a digest:

   ```sh
   python generate_digest.py
   ```

6. Send the digest to all subscribers:

   ```sh
   python send_digest.py
   ```

This will produce a Markdown file in `output/weekly_digest.md` summarising the latest week.

## GitHub Actions

The included workflow (`.github/workflows/run.yml`) runs the scraper,
generates the weekly digest and emails it to all subscribers every Monday at
07:00 America/Toronto time. To enable it, push this repository to GitHub and
configure the repository secrets (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`,
`BREVO_API_KEY`, `STRIPE_SECRET_KEY`).

## Landing page

The `landing/index.html` file contains a simple, static page styled in a Globe‑and‑Mail‑inspired palette of royal blue and light navy.  It explains the value proposition of the Weston Wolverine Brief and includes a form that posts directly to Supabase to collect email addresses.  Edit the JavaScript snippet at the bottom of the file to insert your own `SUPABASE_URL` and `SUPABASE_ANON_KEY`.  Use this page to start gathering early subscribers during your pre‑launch phase.
