from flask import Flask, render_template, request, redirect, url_for
from pathlib import Path
import os

from services.scraper import scrape_all_sites
from services.review_analysis import analyze_reviews
from services.recommender import build_recommendation
from services.video_auth import analyze_video_authenticity

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/compare", methods=["POST"])
def compare():
    product_query = request.form.get("product_query", "").strip()
    video_url = request.form.get("video_url", "").strip()
    preference = request.form.get("preference", "balanced").strip().lower()

    if not product_query:
        return redirect(url_for("home"))

    # Scrape products from all sites
    scraped = scrape_all_sites(product_query)

    # Analyze reviews from scraped products
    review_analysis = analyze_reviews(scraped)

    # Build recommendation
    recommendation = None
    if scraped:
        recommendation = build_recommendation(scraped, review_analysis, preference)

    # Optional video authenticity analysis
    video_result = None
    if video_url:
        try:
            video_result = analyze_video_authenticity(video_url)
        except Exception as e:
            video_result = {
                "status": "error",
                "score": 0.0,
                "explanation": f"Video analysis failed: {str(e)}"
            }

    return render_template(
        "results.html",
        query=product_query,
        products=scraped,
        review_analysis=review_analysis,
        recommendation=recommendation,
        video_result=video_result
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
