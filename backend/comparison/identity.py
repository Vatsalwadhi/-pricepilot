import re
import unicodedata
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class ProductIdentity:
    brand: str
    family: str
    variant: str
    quantity: float
    unit: str

    @property
    def canonical_sku(self) -> str:
        parts = []
        if self.brand: parts.append(self.brand.lower())
        if self.family: parts.append(self.family.lower())
        if self.variant: parts.append(self.variant.lower())
        if self.quantity > 0:
            qty_str = str(self.quantity)
            if qty_str.endswith(".0"):
                qty_str = qty_str[:-2]
            parts.append(qty_str)
        if self.unit: parts.append(self.unit.lower())
        
        raw_slug = "-".join(parts)
        # Remove anything that isn't alphanumeric or hyphen
        cleaned_slug = re.sub(r'[^a-z0-9\-]', '-', raw_slug)
        # Collapse multiple hyphens
        return re.sub(r'-+', '-', cleaned_slug).strip("-")


# Dictionaries for Dairy
BRANDS = [
    "Amul", "Mother Dairy", "Nandini", "Heritage", "Arokya", "Sid's Farm", 
    "Godrej Jersey", "Country Delight", "Humpy Farms", "Akshayakalpa", 
    "FruBon", "Nestle a+", "Nestle", "Govardhan"
]

FAMILIES = {
    "gold": "Gold",
    "taaza": "Taaza",
    "masti": "Masti",
    "good life": "Good Life",
    "goodlife": "Good Life",
    "amrutha": "Amrutha",
    "nourish+": "Nourish+",
    "fit life": "FIT Life",
    "farm fresh": "Farm Fresh",
    "classic": "Classic",
    "moti": "Moti"
}

# Standardized variant names mapped from aliases
VARIANT_MAP = {
    # Full cream
    "full cream milk": "Full Cream Milk",
    "full cream fresh milk": "Full Cream Milk",
    "full cream": "Full Cream Milk",
    
    # Toned
    "homogenised toned milk": "Toned Milk",
    "homogenized toned milk": "Toned Milk",
    "toned fresh milk": "Toned Milk",
    "toned milk": "Toned Milk",
    
    # Double toned
    "homogenized double toned milk": "Double Toned Milk",
    "homogenised double toned milk": "Double Toned Milk",
    "double toned milk": "Double Toned Milk",
    
    # Standardized
    "standardized fresh milk": "Standardized Milk",
    "standardised fresh milk": "Standardized Milk",
    "standardized milk": "Standardized Milk",
    "standardised milk": "Standardized Milk",
    
    # Skimmed
    "skimmed milk": "Skimmed Milk",
    "skim milk": "Skimmed Milk",
    
    # Lactose free
    "lactose free milk": "Lactose Free Milk",
    
    # A2 / Cow / Buffalo
    "a2 cow milk": "A2 Cow Milk",
    "a2 farm organic cow milk": "A2 Cow Milk",
    "a2 pasteurized organic milk": "A2 Cow Milk",
    "a2 pasteurized organic fresh milk": "A2 Cow Milk",
    "organic cow milk": "A2 Cow Milk",
    "buffalo a2 milk": "A2 Buffalo Milk",
    "cow fresh milk": "Cow Milk",
    "cow milk": "Cow Milk",
    
    # Curd / Dahi
    "dahi": "Curd",
    "curd": "Curd",
    
    # Buttermilk
    "spiced salted buttermilk": "Spiced Buttermilk",
    "buttermilk": "Buttermilk",
}

IGNORE_WORDS = [
    "pouch", "pack", "fresh", "tetra", "brick", "brik", "bottle", "jar", "cup", "carton", "tub", "uht", "pasteurized", "pasteurised", "of 2", "of 3", "of 4", "of 6", "1pack", "1pc", "set"
]


def _normalize_string(val: str) -> str:
    if not val: return ""
    text = unicodedata.normalize("NFKD", val).encode("ascii", "ignore").decode().lower()
    # Replace symbols with spaces (except + for Nourish+)
    text = re.sub(r'[^a-z0-9\+]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def extract_quantity_and_unit(text: str) -> Tuple[float, str, str]:
    """
    Returns (numeric_quantity, standardized_unit, text_without_quantity)
    """
    text_clean = text.lower()
    
    # Look for patterns like "500 ml", "1 l", "1.5 kg", "0.5l"
    # We remove it from the text so it doesn't interfere with variant matching
    
    qty_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(ml|l|liter|litre|liters|litres|g|gm|gms|kg|kilogram|kilograms)\b')
    match = qty_pattern.search(text_clean)
    
    qty = 0.0
    unit = ""
    
    if match:
        num = float(match.group(1))
        u = match.group(2)
        
        # Standardize units
        if u in ['l', 'liter', 'litre', 'liters', 'litres']:
            qty = num * 1000
            unit = "ml"
        elif u in ['kg', 'kilogram', 'kilograms']:
            qty = num * 1000
            unit = "g"
        elif u in ['gm', 'gms', 'g']:
            qty = num
            unit = "g"
        elif u == 'ml':
            qty = num
            unit = "ml"
            
        # Remove the matched quantity from text
        text_without_qty = text_clean[:match.start()] + " " + text_clean[match.end():]
        text_without_qty = re.sub(r'\s+', ' ', text_without_qty).strip()
        
        # Sometimes providers specify something like "490ml or 500ml", let's just take the first match which is fine for now,
        # but we should strip all quantities to clean the string
        text_without_qty = qty_pattern.sub('', text_without_qty)
        text_without_qty = re.sub(r'\s+', ' ', text_without_qty).strip()
        
        return qty, unit, text_without_qty

    return 0.0, "", text_clean


def parse_product_identity(name: str, raw_brand: str = "", raw_quantity: str = "") -> ProductIdentity:
    name_clean = _normalize_string(name)
    raw_brand_clean = _normalize_string(raw_brand)
    raw_qty_clean = _normalize_string(raw_quantity)
    
    # 1. Extract Quantity & Unit
    # Try raw_quantity first, then fallback to name
    qty, unit, remaining_qty_text = extract_quantity_and_unit(raw_qty_clean)
    if qty == 0.0:
        qty, unit, name_clean = extract_quantity_and_unit(name_clean)
    else:
        # Still remove quantity from name if it exists there
        _, _, name_clean = extract_quantity_and_unit(name_clean)
        
    # 2. Extract Brand
    brand = ""
    # Check known brands first
    for b in BRANDS:
        b_norm = _normalize_string(b)
        if b_norm in name_clean:
            brand = b
            name_clean = name_clean.replace(b_norm, "")
            break
            
    if not brand and raw_brand:
        # Fallback to provided raw brand
        brand = raw_brand
        
    # 3. Extract Family
    family = ""
    # Sort families by length descending so longer match first, and handle non-word boundaries for symbols
    for f_key in sorted(FAMILIES.keys(), key=len, reverse=True):
        f_val = FAMILIES[f_key]
        # Build pattern that handles symbols at the edges safely
        pattern = r'(?<![a-z0-9])' + re.escape(f_key) + r'(?![a-z0-9])'
        if re.search(pattern, name_clean):
            family = f_val
            name_clean = re.sub(pattern, "", name_clean)
            break
            
    # 4. Extract Variant
    variant = ""
    for v_key in sorted(VARIANT_MAP.keys(), key=len, reverse=True):
        v_val = VARIANT_MAP[v_key]
        pattern = r'(?<![a-z0-9])' + re.escape(v_key) + r'(?![a-z0-9])'
        if re.search(pattern, name_clean):
            variant = v_val
            name_clean = re.sub(pattern, "", name_clean)
            break
            
    # If no variant was found in the dictionary, use whatever is left after stripping ignore words
    if not variant:
        tokens = name_clean.split()
        filtered_tokens = [t for t in tokens if t not in IGNORE_WORDS]
        if filtered_tokens:
            variant = " ".join(filtered_tokens).title()
        else:
            variant = "Unknown"
            
    return ProductIdentity(
        brand=brand,
        family=family,
        variant=variant,
        quantity=qty,
        unit=unit
    )

def is_match(a: ProductIdentity, b: ProductIdentity) -> bool:
    return (
        a.brand == b.brand and
        a.family == b.family and
        a.variant == b.variant and
        a.quantity == b.quantity and
        a.unit == b.unit
    )
