import json
import re
import time
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _clean_price(text: str) -> Optional[float]:
    """
    Clean and extract price from text.
    Handles Indian number format (commas, lakhs, crores).
    Returns price in rupees as float.
    """
    if not text:
        return None
    
    # Remove currency symbols and common text
    text = text.lower().strip()
    text = re.sub(r'[₹$€£]', '', text)
    text = re.sub(r'(rs|rupees?|inr)', '', text)
    
    # Handle lakhs (e.g., "2.5 Lakh" = 250000)
    lakh_match = re.search(r'([\d,]+\.?\d*)\s*lakh', text, re.IGNORECASE)
    if lakh_match:
        try:
            value = float(lakh_match.group(1).replace(',', ''))
            return value * 100000
        except Exception:
            pass
    
    # Handle crores (e.g., "1.5 Crore" = 15000000)
    crore_match = re.search(r'([\d,]+\.?\d*)\s*crore', text, re.IGNORECASE)
    if crore_match:
        try:
            value = float(crore_match.group(1).replace(',', ''))
            return value * 10000000
        except Exception:
            pass
    
    # Extract digits and decimal point, remove commas
    digits = re.sub(r'[^\d.]', '', text)
    if not digits:
        return None
    
    try:
        price = float(digits)
        # Validate: prices should be reasonable (between ₹1 and ₹1 crore for most products)
        if price < 1 or price > 10000000:
            return None
        return price
    except Exception:
        return None


def _validate_and_normalize_prices(products: List[Dict]) -> List[Dict]:
    """
    Validate prices and filter out outliers.
    Removes products with prices that are too far from the median.
    """
    if not products:
        return products
    
    valid_prices = [p.get("price") for p in products if p.get("price") and isinstance(p.get("price"), (int, float))]
    if len(valid_prices) < 2:
        return products
    
    # Calculate median price
    sorted_prices = sorted(valid_prices)
    median = sorted_prices[len(sorted_prices) // 2]
    
    # Calculate standard deviation for better outlier detection
    if len(valid_prices) >= 2:
        mean = sum(valid_prices) / len(valid_prices)
        variance = sum((x - mean) ** 2 for x in valid_prices) / len(valid_prices)
        std_dev = variance ** 0.5
        threshold = mean + (2 * std_dev)  # 2 standard deviations
        min_threshold = mean - (2 * std_dev)
    else:
        threshold = median * 2.5
        min_threshold = median / 2.5
    
    # Filter out prices that are outliers (more than 2.5x median or less than 1/2.5x median)
    # Also filter using standard deviation if available
    # This handles cases where wrong products or prices are scraped
    filtered = []
    for p in products:
        price = p.get("price")
        if price and isinstance(price, (int, float)):
            # Skip if price is too far from median or mean
            if median > 0:
                if price > threshold or price < max(min_threshold, median / 2.5):
                    # Price is an outlier, skip it
                    continue
        filtered.append(p)
    
    return filtered if filtered else products


def _calculate_price_stats(products: List[Dict]) -> Dict:
    """Calculate price statistics for display."""
    prices = [p.get("price") for p in products if p.get("price")]
    if not prices:
        return {}
    
    prices = sorted(prices)
    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)
    median_price = prices[len(prices) // 2]
    
    # Calculate variance percentage
    if median_price > 0:
        variance_pct = ((max_price - min_price) / median_price) * 100
    else:
        variance_pct = 0
    
    return {
        "min": min_price,
        "max": max_price,
        "avg": avg_price,
        "median": median_price,
        "variance_pct": round(variance_pct, 1),
        "count": len(prices)
    }


def _http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 10) -> Optional[str]:
    try:
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept-Language": "en-IN,en;q=0.9",
        }
        if headers:
            default_headers.update(headers)
        resp = requests.get(url, headers=default_headers, timeout=timeout)
        if resp.status_code == 200 and resp.text:
            return resp.text
    except Exception:
        return None
    return None


def scrape_flipkart(query: str) -> Optional[Dict]:
    url = f"https://www.flipkart.com/search?q={requests.utils.quote(query)}"
    html = _http_get(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    # Try common selectors for grid/list cards
    name_el = soup.select_one("div._4rR01T, a.s1Q9rs")
    price_el = soup.select_one("div._30jeq3._1_WHN1, div._30jeq3")
    link_el = soup.select_one("a._1fQZEK, a.s1Q9rs")
    rating_el = soup.select_one("div._3LWZlK")
    if not name_el or not price_el:
        return None
    product_url = url
    if link_el and link_el.get("href"):
        href = link_el.get("href")
        if href and href.startswith("/"):
            product_url = "https://www.flipkart.com" + href

    reviews: List[str] = []
    # Attempt to fetch product page reviews (best-effort)
    product_html = _http_get(product_url)
    if product_html:
        psoup = BeautifulSoup(product_html, "html.parser")
        for sel in [
            "div.t-ZTKy",          # review text container
            "div._6K-7Co",         # older review text
            "div._2-N8zT",         # short excerpts
        ]:
            for el in psoup.select(sel):
                txt = el.get_text(" ", strip=True)
                if txt and txt not in reviews:
                    reviews.append(txt)
                if len(reviews) >= 10:
                    break
            if len(reviews) >= 10:
                break

    return {
        "site": "Flipkart",
        "name": name_el.get_text(strip=True),
        "price": _clean_price(price_el.get_text(strip=True)),
        "rating": float(rating_el.get_text(strip=True)) if rating_el and re.match(r"^[0-9.]+$", rating_el.get_text(strip=True)) else None,
        "url": product_url,
        "reviews": reviews
    }


def scrape_croma(query: str) -> Optional[Dict]:
    url = f"https://www.croma.com/search/?text={requests.utils.quote(query)}"
    html = _http_get(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    name_el = soup.select_one("h3.product-title, a.product-title")
    price_el = soup.select_one("span.new-price, span.amount")
    link_el = soup.select_one("a.product-title, a")
    rating_el = soup.select_one("span.rating, div.rating")
    if not name_el or not price_el:
        return None
    product_url = url
    if link_el and link_el.get("href"):
        href = link_el.get("href")
        if href and href.startswith("/"):
            product_url = "https://www.croma.com" + href

    reviews: List[str] = []
    product_html = _http_get(product_url)
    if product_html:
        psoup = BeautifulSoup(product_html, "html.parser")
        for sel in [
            "p.user-review-desc", "div.user-review-text", "p.review__text",
            "div[class*=review] p", "li[class*=review] p"
        ]:
            for el in psoup.select(sel):
                txt = el.get_text(" ", strip=True)
                if txt and txt not in reviews:
                    reviews.append(txt)
                if len(reviews) >= 10:
                    break
            if len(reviews) >= 10:
                break

    return {
        "site": "Croma",
        "name": name_el.get_text(strip=True),
        "price": _clean_price(price_el.get_text(strip=True)),
        "rating": _clean_price(rating_el.get_text(strip=True)) if rating_el else None,
        "url": product_url,
        "reviews": reviews
    }


def scrape_reliance(query: str) -> Optional[Dict]:
    url = f"https://www.reliancedigital.in/search?q={requests.utils.quote(query)}:relevance"
    html = _http_get(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    name_el = soup.select_one("p.sp__name, p.pdp__title, a")
    price_el = soup.select_one("span.pdp__offerPrice, span.price")
    link_el = soup.select_one("a")
    rating_el = soup.select_one("span.ratings, span.rating")
    if not name_el or not price_el:
        return None
    product_url = url
    if link_el and link_el.get("href"):
        href = link_el.get("href")
        if href and href.startswith("/"):
            product_url = "https://www.reliancedigital.in" + href

    reviews: List[str] = []
    product_html = _http_get(product_url)
    if product_html:
        psoup = BeautifulSoup(product_html, "html.parser")
        for sel in [
            "div[class*=review] p", "p[class*=review]", "li[class*=review] p"
        ]:
            for el in psoup.select(sel):
                txt = el.get_text(" ", strip=True)
                if txt and txt not in reviews:
                    reviews.append(txt)
                if len(reviews) >= 10:
                    break
            if len(reviews) >= 10:
                break

    return {
        "site": "Reliance Digital",
        "name": name_el.get_text(strip=True),
        "price": _clean_price(price_el.get_text(strip=True)),
        "rating": _clean_price(rating_el.get_text(strip=True)) if rating_el else None,
        "url": product_url,
        "reviews": reviews
    }


def _load_sample_data() -> List[Dict]:
    sample_path = BASE_DIR / "data" / "sample_reviews.json"
    try:
        with open(sample_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def scrape_all_sites(query: str) -> List[Dict]:
    results: List[Optional[Dict]] = [
        scrape_flipkart(query),
        scrape_croma(query),
        scrape_reliance(query),
    ]
    cleaned = [r for r in results if r and r.get("price")]
    
    if not cleaned:
        # Try sample data filtered only if relevant; otherwise return no results
        samples = _load_sample_data()
        filtered = [s for s in samples if query.lower() in s.get("name", "").lower()]
        return filtered[:3]
    
    # Validate and normalize prices to remove outliers
    validated = _validate_and_normalize_prices(cleaned)
    
    # Add price statistics to each product for display
    price_stats = _calculate_price_stats(validated)
    for p in validated:
        p["_price_stats"] = price_stats
    
    return validated


