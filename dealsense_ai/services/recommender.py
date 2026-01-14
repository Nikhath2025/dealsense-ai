from typing import Dict, List, Optional


def _score_product(p: Dict, review_summary: Dict, preference: str = "balanced") -> float:
    # Higher score is better. Combine price, rating, and sentiment.
    price = p.get("price") or 0
    rating = p.get("rating") or 0
    # Normalize heuristically: cheaper is better; add value for rating
    price_component = 0.0
    if price > 0:
        price_component = 1.0 / (1.0 + price / 10000.0)  # scales around INR 10k
    rating_component = (rating / 5.0) if rating else 0.5

    # Use global review balance as a small adjustment
    sentiment_boost = 0.0
    if review_summary:
        pos = review_summary.get("positive", 0)
        neg = review_summary.get("negative", 0)
        total = review_summary.get("total_reviews", 0) or 1
        if total > 0:
            sentiment_boost = (pos - neg) / total
            # clamp and scale
            if sentiment_boost > 0:
                sentiment_boost = min(0.2, sentiment_boost * 0.1)
            else:
                sentiment_boost = max(-0.2, sentiment_boost * 0.1)

    # Preference weights
    if preference == "price":
        w_price, w_rating, s_scale = 0.8, 0.2, 1.0
    elif preference == "quality":
        w_price, w_rating, s_scale = 0.3, 0.7, 1.5
    else:
        w_price, w_rating, s_scale = 0.6, 0.4, 1.0

    return price_component * w_price + rating_component * w_rating + sentiment_boost * s_scale


def build_recommendation(products: List[Dict], review_analysis: Dict, preference: str = "balanced") -> Optional[Dict]:
    if not products:
        return None
    scored = [
        {
            **p,
            "score": round(_score_product(p, review_analysis, preference), 3)
        }
        for p in products
        if p.get("price")
    ]
    if not scored:
        return None
    scored_sorted = sorted(scored, key=lambda x: x["score"], reverse=True)
    best = scored_sorted[0]
    return {
        "best": best,
        "ranked": scored_sorted,
        "preference": preference,
        "product": best  # For template compatibility
    }


