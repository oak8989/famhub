from fastapi import APIRouter, Depends
from auth import get_current_user, EMERGENT_LLM_KEY, OPENAI_API_KEY
from database import db
import uuid
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])

# Check if emergentintegrations is available
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    EMERGENT_AVAILABLE = True
except ImportError:
    EMERGENT_AVAILABLE = False
    logger.info("emergentintegrations not available - will use OpenAI fallback")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.info("openai package not available")

AI_SYSTEM_PROMPT = """You are a helpful family chef assistant. Given a list of pantry items, suggest creative and practical meal ideas.

For each suggestion, provide:
- name: The meal name
- description: A brief appetizing description
- difficulty: easy, medium, or hard
- time: Estimated cooking time in minutes
- ingredients: List of ingredients needed (mark which ones they have)
- instructions: Brief cooking steps (3-5 steps)
- tips: Any helpful tips

Respond ONLY with valid JSON in this exact format:
{"meals": [{"name": "...", "description": "...", "difficulty": "easy", "time": 30, "ingredients": ["item (have)", "item (need)"], "instructions": ["Step 1", "Step 2"], "tips": "..."}]}"""


def parse_ai_response(response_text: str) -> dict:
    try:
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            data = json.loads(response_text[json_start:json_end])
            return {"suggestions": data.get("meals", []), "message": "AI suggestions generated!"}
    except json.JSONDecodeError:
        pass
    return {"suggestions": [], "message": "Could not parse AI response"}


@router.get("")
async def get_meal_suggestions(user: dict = Depends(get_current_user)):
    pantry_items = await db.pantry_items.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    recipes = await db.recipes.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    pantry_names = [p["name"].lower() for p in pantry_items]
    suggestions = []
    for recipe in recipes:
        recipe_ingredients = [i.lower() for i in recipe.get("ingredients", [])]
        matches = sum(1 for ing in recipe_ingredients if any(p in ing for p in pantry_names))
        total = len(recipe_ingredients) if recipe_ingredients else 1
        match_percent = (matches / total) * 100
        if matches > 0:
            suggestions.append({
                "recipe": recipe,
                "matches": matches,
                "total_ingredients": total,
                "match_percent": round(match_percent, 1),
                "missing": [ing for ing in recipe_ingredients if not any(p in ing for p in pantry_names)]
            })
    suggestions.sort(key=lambda x: x["match_percent"], reverse=True)
    return suggestions[:10]


@router.post("/ai")
async def get_ai_meal_suggestions(user: dict = Depends(get_current_user)):
    pantry_items = await db.pantry_items.find({"family_id": user["family_id"]}, {"_id": 0}).to_list(1000)
    if not pantry_items:
        return {"suggestions": [], "message": "Add items to your pantry first!"}

    pantry_names = [f"{p['name']} ({p.get('quantity', 1)} {p.get('unit', 'pcs')})" for p in pantry_items]

    # Find items expiring soon to prioritize
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    expiring_soon = []
    for p in pantry_items:
        if p.get("expiry_date"):
            try:
                exp = datetime.fromisoformat(p["expiry_date"].replace("Z", "+00:00")) if "T" in p["expiry_date"] else datetime.strptime(p["expiry_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if exp - now < timedelta(days=5):
                    expiring_soon.append(p["name"])
            except (ValueError, TypeError):
                pass

    # Get recent meal plans to avoid repetition
    recent_meals = await db.meal_plans.find({"family_id": user["family_id"]}, {"_id": 0, "recipe_name": 1}).sort("date", -1).to_list(10)
    recent_names = [m.get("recipe_name", "") for m in recent_meals if m.get("recipe_name")]

    prompt = f"""Based on these pantry items, suggest 3-4 creative meal ideas that can be made:

Pantry items: {', '.join(pantry_names)}"""

    if expiring_soon:
        prompt += f"\n\nPRIORITY - Use these items first (expiring soon): {', '.join(expiring_soon)}"

    if recent_names:
        prompt += f"\n\nAvoid repeating these recent meals: {', '.join(recent_names[:5])}"

    prompt += "\n\nFocus on meals that use mostly what's available. Mark ingredients as \"(have)\" if they're in the pantry, \"(need)\" if they need to be bought."

    if EMERGENT_AVAILABLE and EMERGENT_LLM_KEY:
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"meal-suggestion-{user['family_id']}-{uuid.uuid4()}",
                system_message=AI_SYSTEM_PROMPT
            ).with_model("openai", "gpt-4o-mini")
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            return parse_ai_response(response)
        except Exception as e:
            logger.error(f"Emergent AI error: {e}")

    if OPENAI_AVAILABLE and OPENAI_API_KEY:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": AI_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000
            )
            return parse_ai_response(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return {"suggestions": [], "message": f"AI service error: {str(e)}"}

    if not EMERGENT_LLM_KEY and not OPENAI_API_KEY:
        return {"suggestions": [], "message": "AI not configured. Add OPENAI_API_KEY to enable AI meal suggestions."}
    return {"suggestions": [], "message": "AI service unavailable. Please try again later."}
