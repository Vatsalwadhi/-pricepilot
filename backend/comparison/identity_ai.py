import os
import json
import logging
import google.generativeai as genai
from django.conf import settings
from .identity import parse_product_identity, _normalize_string
from api.models import ProductIdentityCache
from providers.base import ProductOffer

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Extract ONLY JSON.

{
  "brand": "",
  "family": "",
  "variant": "",
  "flavour": "",
  "size": "",
  "unit": "",
  "category": "",
  "canonical_name": "",
  "confidence": 0.0
}

Rules:

Ignore:

Pack
Pouch
Fresh
Brick
Bottle
Jar
Combo
Offer
Free

Normalize units.

0.5L -> 500ml

1 litre -> 1000ml

Treat spelling differences as identical.

Taaza = Taza

Homogenised = Homogenized

Do NOT invent information.

Return JSON only."""

def get_cache_key(raw_title: str) -> str:
    return _normalize_string(raw_title)

def call_gemini(brand: str, title: str, quantity: str, category: str, platform: str) -> dict:
    payload = {
        "brand": brand,
        "title": title,
        "platform": platform
    }
    if quantity:
        payload["quantity"] = quantity
    if category:
        payload["category"] = category
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
        
    genai.configure(api_key=api_key)
    
    # We use gemini-2.5-flash
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
        generation_config=genai.types.GenerationConfig(
            temperature=0.0,
            response_mime_type="application/json",
        )
    )
    
    response = model.generate_content(json.dumps(payload))
    content = response.text.strip()
    
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    return json.loads(content)

def is_valid(llm_output: dict, fallback_identity, original_title: str) -> bool:
    # 1. Check confidence
    confidence = float(llm_output.get("confidence", 0.0))
    if confidence < 0.90:
        logger.warning(f"Validation failed (Confidence {confidence} < 0.90) for {original_title}")
        return False
        
    # 2. Check required fields
    required = ["brand", "family", "variant", "flavour", "size", "unit", "canonical_name"]
    for req in required:
        if req not in llm_output:
            logger.warning(f"Validation failed (Missing field {req}) for {original_title}")
            return False
            
    # 3. Brand matches parsed brand (if parsed brand found it)
    if fallback_identity.brand and str(llm_output.get("brand", "")).lower() not in fallback_identity.brand.lower():
        # Allow slight leniency if one is substring of other (e.g. "Amul" vs "Amul Dairy"), but strict mostly
        logger.warning(f"Validation failed (Brand mismatch: {llm_output.get('brand')} vs {fallback_identity.brand}) for {original_title}")
        return False
        
    # 4. Quantity differs by more than 5%
    try:
        llm_qty = float(llm_output.get("size", 0.0) or 0.0)
    except ValueError:
        llm_qty = 0.0
        
    llm_unit = str(llm_output.get("unit", "")).lower()
    
    if llm_unit in ['l', 'liter', 'litre', 'liters', 'litres']:
        llm_qty *= 1000
        llm_unit = "ml"
    elif llm_unit in ['kg', 'kilogram', 'kilograms']:
        llm_qty *= 1000
        llm_unit = "g"
        
    if fallback_identity.quantity > 0:
        if llm_unit != fallback_identity.unit:
            logger.warning(f"Validation failed (Unit mismatch: {llm_unit} vs {fallback_identity.unit}) for {original_title}")
            return False
            
        diff = abs(llm_qty - fallback_identity.quantity)
        if diff > (0.05 * fallback_identity.quantity):
            logger.warning(f"Validation failed (Quantity mismatch: {llm_qty} vs {fallback_identity.quantity}) for {original_title}")
            return False
            
    return True

def normalize_product(offer: ProductOffer):
    raw_title = offer.product_name
    cache_key = get_cache_key(raw_title)
    
    raw_brand = offer.raw_payload.get("brand") or offer.raw_payload.get("brand_name") or ""
    fallback_identity = parse_product_identity(raw_title, raw_brand, offer.quantity)
    
    cached = ProductIdentityCache.objects.filter(cache_key=cache_key).first()
    if cached:
        if os.getenv("DEBUG_IDENTITY") == "1":
            print(f"\n[CACHE HIT] {raw_title}\n -> \n{cached.canonical_name}\n -> \nConfidence: {cached.confidence}")
        
        return {
            "brand": cached.brand,
            "family": cached.family,
            "variant": cached.variant,
            "flavour": cached.flavour,
            "size": cached.size,
            "unit": cached.unit,
            "canonical_name": cached.canonical_name,
            "category": cached.category,
            "confidence": cached.confidence
        }
        
    try:
        raw_category = offer.raw_payload.get("category", "")
        
        llm_output = call_gemini(raw_brand, raw_title, offer.quantity, raw_category, offer.platform)
        
        if not is_valid(llm_output, fallback_identity, raw_title):
            raise ValueError(f"LLM validation failed: {json.dumps(llm_output)}")
            
        try:
            parsed_size = float(llm_output.get("size", 0.0) or 0.0)
        except ValueError:
            parsed_size = 0.0
            
        identity = {
            "brand": llm_output.get("brand", ""),
            "family": llm_output.get("family", ""),
            "variant": llm_output.get("variant", ""),
            "flavour": llm_output.get("flavour", ""),
            "size": parsed_size,
            "unit": llm_output.get("unit", ""),
            "category": llm_output.get("category", ""),
            "canonical_name": llm_output.get("canonical_name", ""),
            "confidence": float(llm_output.get("confidence", 1.0))
        }
        
        ProductIdentityCache.objects.update_or_create(
            cache_key=cache_key,
            defaults={
                "raw_title": raw_title,
                **identity
            }
        )
        
        if os.getenv("DEBUG_IDENTITY") == "1":
            print(f"\n[CACHE MISS] {raw_title}\n -> \n{identity['canonical_name']}\n -> \nConfidence: {identity['confidence']}")
            
        return identity
        
    except Exception as e:
        logger.error(f"Fallback Used for {raw_title}. Reason: {str(e)}")
        
        if os.getenv("DEBUG_IDENTITY") == "1":
            print(f"\n[FALLBACK] {raw_title}\n -> \n{fallback_identity.canonical_sku}\n -> \nReason: {str(e)}")
            
        return {
            "brand": fallback_identity.brand,
            "family": fallback_identity.family,
            "variant": fallback_identity.variant,
            "flavour": "",
            "size": fallback_identity.quantity,
            "unit": fallback_identity.unit,
            "category": "",
            "canonical_name": fallback_identity.canonical_sku,
            "confidence": 1.0
        }
