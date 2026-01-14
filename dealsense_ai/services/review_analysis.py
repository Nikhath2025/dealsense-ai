from typing import Dict, List
import re

try:
    from textblob import TextBlob
except ImportError:
    # Fallback if TextBlob is not available
    TextBlob = None

KEYWORDS = ["quality", "price", "delivery", "performance", "battery", "camera"]


def extract_context(review: str, keywords: List[str] = KEYWORDS) -> Dict[str, str]:
    """Extract context around keywords in reviews (3 words before and after)."""
    context_dict = {}
    review_lower = review.lower()
    for kw in keywords:
        if kw.lower() in review_lower:
            # Find the keyword and extract surrounding context
            pattern = rf'(\S+\s+){{0,3}}{re.escape(kw)}(\s+\S+){{0,3}}'
            match = re.search(pattern, review, re.IGNORECASE)
            if match:
                context_dict[kw] = match.group().strip()
    return context_dict


def sentiment_analysis(review: str) -> float:
    """Simple polarity check using TextBlob."""
    if TextBlob:
        try:
            score = TextBlob(review).sentiment.polarity
            return round(score, 2)
        except Exception:
            pass
    # Fallback: simple keyword-based sentiment
    positive_words = ["good", "great", "excellent", "amazing", "satisfied", "happy", "recommended", "genuine", "fast"]
    negative_words = ["bad", "poor", "disappointed", "defective", "slow", "issues", "high"]
    review_lower = review.lower()
    pos_count = sum(1 for word in positive_words if word in review_lower)
    neg_count = sum(1 for word in negative_words if word in review_lower)
    if pos_count > neg_count:
        return 0.3
    elif neg_count > pos_count:
        return -0.3
    return 0.0


def analyze_reviews(products: List[Dict]) -> Dict:
    """
    Analyze reviews from products list.
    Expects each product dict to optionally include a 'reviews' list of strings.
    """
    all_reviews = []
    for p in products or []:
        for r in (p.get("reviews") or []):
            if isinstance(r, str) and r.strip():
                all_reviews.append(r.strip())

    if not all_reviews:
        return {
            "avg_rating": 0.0,
            "total_reviews": 0,
            "summary": "No reviews available for analysis.",
            "positive": 0,
            "negative": 0,
            "neutral": 0
        }

    per_review = []
    counts = {"positive": 0, "negative": 0, "neutral": 0}
    
    for r in all_reviews:
        score = sentiment_analysis(r)
        if score > 0.1:
            counts["positive"] += 1
        elif score < -0.1:
            counts["negative"] += 1
        else:
            counts["neutral"] += 1
        
        per_review.append({
            "review": r,
            "sentiment": score,
            "context": extract_context(r)
        })

    # Calculate average rating from product ratings if available
    ratings = [p.get("rating") for p in products if p.get("rating")]
    avg_rating = sum(ratings) / len(ratings) if ratings else 0.0

    # Generate summary
    total = len(all_reviews)
    pos_pct = (counts["positive"] / total * 100) if total > 0 else 0
    summary = f"Analysis of {total} reviews: {pos_pct:.0f}% positive, {counts['negative']} negative, {counts['neutral']} neutral."

    return {
        "avg_rating": round(avg_rating, 1),
        "total_reviews": total,
        "summary": summary,
        "positive": counts["positive"],
        "negative": counts["negative"],
        "neutral": counts["neutral"],
        "details": per_review
    }

