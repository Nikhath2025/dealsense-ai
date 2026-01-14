# DealSense AI

India-first product comparison website that scrapes prices and ratings from multiple e-commerce sites, analyzes review sentiment with 3-word context windows, and heuristically scores review video authenticity.

## Problem Statement
Online shoppers face fragmented pricing across Indian e-commerce platforms and unreliable reviews (including AI-generated media). There is no single place to compare prices, assess review quality with context, and validate the authenticity of review videos.

## Objective
- Build a web app to compare products across India-specific sites (Flipkart, Croma, Reliance Digital).
- Analyze reviews with keyword polarity and 3-word context windows around keywords.
- Estimate review video authenticity.
- Deliver an attractive dark-themed UI suited for hackathon demos.

## Solution Overview
- Backend: Python (Flask).
- Frontend: HTML/CSS (dark theme).
- Scraping: Requests + BeautifulSoup with headers and graceful fallbacks.
- Review Analysis: Simple lexicon-based polarity with context windows.
- Video Authenticity: Heuristic score based on textual signals and hosting hints (no heavy ML).
- Fallback: Ships with `data/sample_reviews.json` for reliable demo even if live scraping is blocked.

## Technical Approach
- Scrape 3 sites (Flipkart, Croma, Reliance) using common selectors, robust headers, and timeouts.
- Normalize price, parse ratings, and aggregate into a comparable list.
- Analyze reviews: tokenize, detect positive/negative keywords, extract 3-word windows around each keyword.
- Recommend best deal by combining normalized price, rating, and global sentiment balance.
- Check video authenticity heuristically (flags: suspicious hosts, obvious AI terms, short-form platforms).

## Project Structure
```
.
├── app.py
├── services
│   ├── scraper.py
│   ├── review_analysis.py
│   ├── video_auth.py
│   └── recommender.py
├── templates
│   ├── base.html
│   ├── index.html
│   └── results.html
├── static
│   └── css
│       └── style.css (dark theme)
├── data
│   └── sample_reviews.json
├── requirements.txt
└── README.md
```

## Steps to Execute
1. Create and activate a virtual environment (Windows PowerShell):
```powershell
cd .\dealsense_ai
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
```
2. Install dependencies:
```powershell
pip install -r requirements.txt
```
3. Run the server:
```powershell
python app.py
```
4. Open in browser: `http://localhost:5000`

## Tools, Libraries, Dependencies
- Flask (web server and templating)
- Requests (HTTP)
- BeautifulSoup4 (HTML parsing)

## Prototype Notes (Real Data & Demo)
- The scraper targets public search pages. Some sites may block bot traffic; the app auto-falls back to real sample data in `data/sample_reviews.json` (actual product/price-like data) so your demo always works.
- For live comparisons, try general queries like "iPhone 15", "Samsung Galaxy", "LG TV".
- The video authenticity checker is heuristic (fast, no GPU) and flags suspicious patterns in the provided URL/path.

## Limitations & Future Work
- JS-rendered reviews are not deeply scraped; integrate Selenium or requests-html if needed.
- Add stronger ML sentiment models and true deepfake detection when GPU/weights are available.
- Improve site-specific selectors and add more Indian e-commerce sources.


