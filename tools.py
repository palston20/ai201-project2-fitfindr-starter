"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# Chat model used by the LLM-backed tools. Change this in one place if the
# model is retired or a different one is preferred.
_MODEL = "openai/gpt-oss-120b"


def _ask_llm(system: str, user: str, temperature: float = 0.7,
             max_tokens: int = 1000) -> str:
    """Send one system + user prompt to the chat model and return the text."""
    client = _get_groq_client()
    response = client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (response.choices[0].message.content or "").strip()


# ── Tool 1: search_listings ───────────────────────────────────────────────────

# Words that carry no signal about what the user actually wants.
_STOPWORDS = {
    "a", "an", "and", "any", "are", "as", "at", "be", "but", "by", "can", "find",
    "for", "from", "get", "i", "if", "in", "is", "it", "like", "looking", "me",
    "my", "need", "of", "on", "or", "please", "show", "some", "something", "that",
    "the", "then", "there", "this", "to", "under", "up", "want", "was", "what",
    "with", "would", "you", "your",
}

# Fields that are searched, and how much a hit in each one is worth.
_FIELD_WEIGHTS = (
    ("title", 3),
    ("style_tags", 3),
    ("category", 2),
    ("colors", 2),
    ("brand", 2),
    ("description", 1),
)


def _singular(word: str) -> str:
    """Fold a simple plural so 'tees' and 'tee' score as the same keyword."""
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _keywords(value) -> set[str]:
    """Turn a string (or list of strings) into a set of comparable keywords."""
    if value is None:
        return set()
    if isinstance(value, (list, tuple)):
        value = " ".join(str(v) for v in value)
    words = re.findall(r"[a-z0-9']+", str(value).lower())
    return {_singular(w) for w in words if len(w) > 1 and w not in _STOPWORDS}


def _size_matches(listing_size: str | None, wanted: str) -> bool:
    """
    True if `wanted` appears as a whole size component of `listing_size`.

    Sizes in the dataset are inconsistent ("S/M", "XL (oversized)", "W30 L30",
    "US 8.5"), so the wanted size has to match on a component boundary rather
    than as a plain substring: "M" matches "S/M" and "M/L", but "S" does not
    match "One Size" and "US 8" does not match "US 8.5".
    """
    if not listing_size:
        return False
    pattern = r"(?<![A-Za-z0-9.])" + re.escape(wanted.strip()) + r"(?![A-Za-z0-9.])"
    return re.search(pattern, str(listing_size), re.IGNORECASE) is not None


def _relevance_score(listing: dict, wanted: set[str]) -> int:
    """Score a listing by weighted keyword overlap with the user's description."""
    score = 0
    for field, weight in _FIELD_WEIGHTS:
        score += weight * len(wanted & _keywords(listing.get(field)))
    return score


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    listings = load_listings()

    wanted = _keywords(description)
    if not wanted:
        # Nothing to match on, so nothing can score above 0.
        return []

    scored: list[tuple[int, float, dict]] = []
    for listing in listings:
        price = listing.get("price")
        if max_price is not None and (price is None or price > max_price):
            continue

        if size and size.strip() and not _size_matches(listing.get("size"), size):
            continue

        score = _relevance_score(listing, wanted)
        if score == 0:
            # No keyword overlap — not a real match.
            continue

        scored.append((score, price if price is not None else 0.0, listing))

    # Best match first; cheaper listing wins a tie so the order is stable.
    scored.sort(key=lambda row: (-row[0], row[1]))
    return [listing for _, _, listing in scored]

    print(search_listings("Y2K pink top", "M", 20))


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

_STYLIST_SYSTEM_PROMPT = (
    "You are FitFindr, a friendly secondhand-fashion stylist. "
    "You help people picture how a thrifted find would actually work in real life. "
    "Write in plain, casual language \u2014 no bullet-point catalogues, no hype, "
    "no markdown headings. Be concrete about colour, fit and silhouette."
)


def _describe_item(item: dict) -> str:
    """Format a listing dict into a compact block of prompt text."""
    parts = [f"Item: {item.get('title') or 'Untitled item'}"]
    for label, key in (("Category", "category"), ("Brand", "brand"),
                       ("Size", "size"), ("Condition", "condition")):
        value = item.get(key)
        if value:
            parts.append(f"{label}: {value}")
    for label, key in (("Colors", "colors"), ("Style", "style_tags")):
        values = item.get(key)
        if values:
            parts.append(f"{label}: {', '.join(str(v) for v in values)}")
    price = item.get("price")
    if price is not None:
        parts.append(f"Price: ${price:.2f} on {item.get('platform') or 'a resale site'}")
    if item.get("description"):
        parts.append(f"Seller's notes: {item['description']}")
    return "\n".join(parts)


def _format_wardrobe(items: list[dict]) -> str:
    """Format wardrobe items as a category-grouped list the LLM can cite by name."""
    by_category: dict[str, list[str]] = {}
    for entry in items:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not name:
            continue
        details = []
        colors = entry.get("colors")
        if colors:
            details.append(", ".join(str(c) for c in colors))
        tags = entry.get("style_tags")
        if tags:
            details.append(", ".join(str(t) for t in tags))
        if entry.get("notes"):
            details.append(str(entry["notes"]))
        suffix = f" ({'; '.join(details)})" if details else ""
        category = str(entry.get("category") or "other")
        by_category.setdefault(category, []).append(f"  - {name}{suffix}")

    lines = []
    for category in sorted(by_category):
        lines.append(f"{category.capitalize()}:")
        lines.extend(by_category[category])
    return "\n".join(lines)


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    item_block = _describe_item(new_item or {})

    items = (wardrobe or {}).get("items") or []
    closet = _format_wardrobe(items) if items else ""

    if not closet:
        # Empty wardrobe (or no usable entries): fall back to general advice
        # instead of returning nothing.
        prompt = (
            f"{item_block}\n\n"
            "The shopper has not told us anything about their existing wardrobe, "
            "so you cannot name pieces they own. Give general styling advice for "
            "this item instead:\n"
            "- Sketch 1-2 complete outfit ideas around it, describing the other "
            "pieces by type, colour and fit (for example 'a fitted black tank' "
            "rather than a specific item they own).\n"
            "- Say what vibe or occasion each look suits.\n"
            "- Mention which colours and silhouettes pair well with it.\n"
            "Keep it under 150 words and do not claim they already own anything."
        )
    else:
        prompt = (
            f"{item_block}\n\n"
            f"The shopper's current wardrobe:\n{closet}\n\n"
            "Suggest 1-2 complete outfits built around the thrifted item above.\n"
            "- Every other piece in an outfit must be one the shopper already "
            "owns, referred to by its exact name from the wardrobe list.\n"
            "- Never invent a piece that is not on that list.\n"
            "- Give each outfit a short label, then a sentence or two on why it "
            "works and when to wear it.\n"
            "Keep it under 180 words."
        )

    try:
        suggestion = _ask_llm(_STYLIST_SYSTEM_PROMPT, prompt, temperature=0.7)
    except Exception as exc:  # network error, bad key, model unavailable
        return (
            "Could not generate an outfit suggestion right now "
            f"({type(exc).__name__}: {exc}). Please try again."
        )

    if not suggestion:
        return (
            "Could not generate an outfit suggestion right now "
            "(the model returned an empty response). Please try again."
        )
    return suggestion


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

_CAPTION_SYSTEM_PROMPT = (
 " In 2 to 3 short sentences, around 10-20 words total. Keep it punchy and social-media-ready. "
"Naturally mention the item's name, price, and platform once each. "
"Briefly capture the outfit vibe using specific details like the colors, silhouette, "
"or overall aesthetic. No hashtags or emoji spam, but 1-2 emojis are allowed."
"Don't sound like a product description or a generic hype post. Vary the opening and sentence structure each time."
)

# How hot to run the caption model. Captions should read differently for
# different items (and on repeat runs), so this is well above the 0.7 used
# for outfit suggestions.
_CAPTION_TEMPERATURE = 1.1


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not isinstance(outfit, str) or not outfit.strip():
        return (
            "Cannot write a fit card without an outfit suggestion. "
            "Run suggest_outfit() first and pass its result in as `outfit`."
        )

    item = new_item or {}

    # Only ask for details the listing actually has, so the caption never
    # invents a price or a platform.
    must_mention = []
    if item.get("title"):
        must_mention.append(f'the item by name ("{item["title"]}")')
    if item.get("price") is not None:
        must_mention.append(f'the price (${item["price"]:.2f})')
    if item.get("platform"):
        must_mention.append(f'where it came from ({item["platform"]})')
    mentions = (
        "Work in " + ", ".join(must_mention) + " \u2014 once each, worked into the "
        "sentences naturally rather than listed off."
        if must_mention else
        "Keep it about the look itself; you have no reliable item details to cite."
    )

    prompt = (
        f"{_describe_item(item)}\n\n"
        f"How it is being styled:\n{outfit.strip()}\n\n"
        "Write the caption for this outfit post.\n"
        f"- {mentions}\n"
        "- Name the actual vibe of the look in specific terms \u2014 the colours, "
        "the silhouette, where you would wear it. No generic hype words like "
        "'stunning', 'obsessed', 'must-have'.\n"
        "- 2 to 4 sentences. No hashtags, no emoji spam, no markdown.\n"
        "- Vary how you open. Do not start with the same word or construction "
        "you would reach for by default.\n"
        "Return only the caption text."
    )

    try:
        caption = _ask_llm(
            _CAPTION_SYSTEM_PROMPT,
            prompt,
            temperature=_CAPTION_TEMPERATURE,
            # Generous budget: the model spends part of it on hidden reasoning
            # before writing, and a starved budget returns empty content.
            max_tokens=1000,
        )
    except Exception as exc:  # network error, bad key, model unavailable
        return (
            "Could not generate a fit card right now "
            f"({type(exc).__name__}: {exc}). Please try again."
        )

    if not caption:
        return (
            "Could not generate a fit card right now "
            "(the model returned an empty response). Please try again."
        )
    return caption
