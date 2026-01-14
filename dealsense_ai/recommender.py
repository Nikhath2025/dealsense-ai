def build_recommendation(products, preference):
    if not products:
        return None

    best = min(products, key=lambda x: x["price"])

    return {
        "product": best,
        "reason": f"Best price based on your preference: {preference}"
    }
