from typing import Dict
import re

# Lightweight heuristic video authenticity check.
# This avoids heavy ML dependencies and works offline.
# It inspects the URL/file hint pattern and returns a score with an explanation.


def analyze_video_authenticity(video_url_or_path: str) -> Dict:
    text = (video_url_or_path or "").lower()

    red_flags = [
        (r"deepfake|ai.*generated|synthetic", 0.4, "Text suggests AI generation"),
        (r"\.gif$", 0.2, "Animated GIF is not a real review video"),
        (r"\.mp4|\.mov|\.mkv", 0.0, "Standard video container"),
        (r"tiktok|instagram|reels", 0.1, "Short-form platform, higher risk of edits"),
        (r"drive\.google|we\.tl|anonfiles", 0.15, "Untrusted hosting"),
    ]

    score = 1.0
    reasons = []
    for pattern, penalty, reason in red_flags:
        if re.search(pattern, text):
            score -= penalty
            if penalty > 0:
                reasons.append(reason)

    score = max(0.0, min(1.0, score))
    status = "likely_real" if score >= 0.7 else ("uncertain" if score >= 0.4 else "likely_ai_or_fake")
    explanation = "; ".join(reasons) if reasons else "No obvious red flags detected"
    return {
        "status": status,
        "score": round(score, 2),
        "explanation": explanation
    }






