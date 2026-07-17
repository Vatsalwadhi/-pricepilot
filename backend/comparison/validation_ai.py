import json
import logging
import requests
from api.models import ProductValidationCache

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are validating whether two grocery products represent the SAME product.

Ignore differences like:
- spacing
- punctuation
- capitalisation
- "500 ml" vs "500ml"
- "Homogenised" vs "Homogenized"
- "Pack"
- "Pouch"
- "Fresh"
- "Tetra Pack"
- "Brick"

DO NOT ignore:
- Brand
- Quantity
- Unit
- Variant
- Flavour
- Fat type
- Category

CRITICAL RULES:
1. If the products belong to fundamentally DIFFERENT categories (e.g., Lemons vs Onions, Carrots vs Potatoes, Rice vs Wheat), they are ALWAYS DIFFERENT. Return false immediately.
2. If the products are of the same type but different brands (e.g., Amul Milk vs Mother Dairy Milk), they are DIFFERENT. Return false.
3. If one product is a specific variant and the other is a completely different vegetable/fruit/item, they are DIFFERENT. Return false.

Examples:

Amul Gold Full Cream Milk 500ml
Amul Gold Full Cream Milk 500 ml
→ SAME

Amul Gold Full Cream Milk 500ml
Amul Gold Full Cream Milk 1L
→ DIFFERENT

Amul Gold
Amul Taaza
→ DIFFERENT

Amul Gold
Mother Dairy Full Cream
→ DIFFERENT

Return ONLY JSON.

{
    "same_product": true,
    "confidence": 0.98,
    "reason": "Only formatting differences"
}"""

def call_llm_validation(product_a: str, product_b: str) -> dict:
    prompt = f"Product A:\n{product_a}\n\nProduct B:\n{product_b}\n\nReturn JSON output."
    
    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "mistral",
                "system": SYSTEM_PROMPT,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            },
            timeout=30
        )
        response.raise_for_status()
        content = response.json().get("response", "")
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        return json.loads(content)
    except Exception as e:
        logger.error(f"Local LLM generation error for validation: {e}")
        return {
            "same_product": False,
            "confidence": 0.0,
            "reason": f"Error: {str(e)}"
        }

def evaluate_pairwise_match(product_a_raw: str, product_b_raw: str) -> dict:
    # Ensure consistent ordering for cache key
    if product_a_raw > product_b_raw:
        product_a_raw, product_b_raw = product_b_raw, product_a_raw

    cached = ProductValidationCache.objects.filter(
        product_a_raw=product_a_raw,
        product_b_raw=product_b_raw
    ).first()

    if cached:
        return {
            "same_product": cached.same_product,
            "confidence": cached.confidence,
            "reason": cached.reason,
        }
        
    # Cache miss
    output = call_llm_validation(product_a_raw, product_b_raw)
    
    try:
        ProductValidationCache.objects.create(
            product_a_raw=product_a_raw,
            product_b_raw=product_b_raw,
            same_product=output.get("same_product", False),
            confidence=output.get("confidence", 0.0),
            reason=output.get("reason", ""),
        )
    except Exception as e:
        logger.error(f"Failed to cache validation {product_a_raw} vs {product_b_raw}: {e}")

    return output
