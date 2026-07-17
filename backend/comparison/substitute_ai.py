import json
import logging
import os
import google.generativeai as genai
from api.models import SubstituteCache
from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are building a grocery comparison engine.

Determine whether two grocery products should be compared side-by-side.

Two products SHOULD be comparable if a customer would reasonably consider them alternatives while shopping.

Examples:

Amul Gold 500ml
Mother Dairy Full Cream 500ml

→ Comparable

Amul Taaza 500ml
Mother Dairy Toned Milk 500ml

→ Comparable

Amul Gold 500ml
Amul Gold 1L

→ Comparable but lower score

Amul Gold
Amul Taaza

→ Comparable but note different variant

Amul Gold
Amul Cheese

→ Never comparable

Return JSON only.

{
  "comparable": true,
  "score": 0.94,
  "reason": "...",
  "same_brand": false,
  "same_variant": true,
  "same_quantity": true,
  "same_category": true,
  "preferred_match": true
}"""

def call_gemini_substitute(product_a: str, product_b: str) -> dict:
    prompt = f"Product A:\n{product_a}\n\nProduct B:\n{product_b}\n\nReturn JSON output."
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
    genai.configure(api_key=api_key)
    
    generation_config = {
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 1024,
        "response_mime_type": "application/json",
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=generation_config,
        system_instruction=SYSTEM_PROMPT,
    )

    try:
        response = model.generate_content(prompt)
        content = response.text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        return json.loads(content)
    except Exception as e:
        logger.error(f"Gemini generation error for substitutes: {e}")
        return {
            "comparable": False,
            "score": 0.0,
            "reason": f"Error: {str(e)}",
            "same_brand": False,
            "same_variant": False,
            "same_quantity": False,
            "same_category": False,
            "preferred_match": False
        }

def evaluate_substitute(product_a_name: str, product_b_name: str) -> dict:
    # Ensure consistent ordering for cache key
    if product_a_name > product_b_name:
        product_a_name, product_b_name = product_b_name, product_a_name

    cached = SubstituteCache.objects.filter(
        product_a_name=product_a_name,
        product_b_name=product_b_name
    ).first()

    if cached:
        return {
            "comparable": cached.comparable,
            "score": cached.score,
            "reason": cached.reason,
            "same_brand": cached.same_brand,
            "same_variant": cached.same_variant,
            "same_quantity": cached.same_quantity,
            "same_category": cached.same_category,
            "preferred_match": cached.preferred_match,
        }
        
    # Cache miss
    output = call_gemini_substitute(product_a_name, product_b_name)
    
    try:
        SubstituteCache.objects.create(
            product_a_name=product_a_name,
            product_b_name=product_b_name,
            comparable=output.get("comparable", False),
            score=output.get("score", 0.0),
            reason=output.get("reason", ""),
            same_brand=output.get("same_brand", False),
            same_variant=output.get("same_variant", False),
            same_quantity=output.get("same_quantity", False),
            same_category=output.get("same_category", False),
            preferred_match=output.get("preferred_match", False),
        )
    except Exception as e:
        logger.error(f"Failed to cache substitute {product_a_name} vs {product_b_name}: {e}")

    return output
