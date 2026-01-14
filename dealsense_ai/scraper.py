def scrape_all_sites(query):
    return [
        {
            "name": f"{query} – Flipkart",
            "price": 49999,
            "source": "Flipkart",
            "url": "https://www.flipkart.com",
            "rating": 4.3
        },
        {
            "name": f"{query} – Croma",
            "price": 50599,
            "source": "Croma",
            "url": "https://www.croma.com",
            "rating": 4.2
        },
        {
            "name": f"{query} – Reliance Digital",
            "price": 49799,
            "source": "Reliance Digital",
            "url": "https://www.reliancedigital.in",
            "rating": 4.1
        }
    ]


