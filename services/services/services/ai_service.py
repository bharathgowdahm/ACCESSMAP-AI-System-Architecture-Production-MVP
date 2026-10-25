"""Optional Gemini Multi-Modal and Conversational Assistance with Deterministic Fallback."""
from core.config import get_settings
from PIL import Image

settings = get_settings()


class AccessGuideAIService:

    @classmethod
    def get_client(cls):
        if not settings.GEMINI_API_KEY:
            return None
        try:
            from google import genai
            return genai.Client(api_key=settings.GEMINI_API_KEY)
        except Exception:
            return None

    @classmethod
    def answer_accessibility_query(cls, user_prompt: str, context_json: str) -> str:
        """Answers queries grounded strictly in verified navigation data."""
        client = cls.get_client()
        if not client:
            return (
                "AccessGuide AI (Deterministic Mode): I am operating offline without Gemini API credentials. "
                "Based on system state, your route has been evaluated using AccessDNA™ algorithms. "
                "Review the breakdown tab for exact step-free and slope metrics."
            )
        try:
            system_instruction = (
                "You are AccessGuide AI, an accessibility navigation assistant. "
                "Base answers strictly on the provided context JSON. Never invent elevator availability, "
                "curb ramps, or flat walkways if missing. Always disclose uncertainty."
            )
            prompt = f"Context Data: {context_json}\nUser Question: {user_prompt}"
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"system_instruction": system_instruction, "temperature": 0.2}
            )
            return response.text
        except Exception as exc:
            return f"AccessGuide AI is momentarily unavailable ({exc}). Relying on deterministic AccessDNA™ metrics."

    @classmethod
    def analyze_barrier_photo(cls, image: Image.Image) -> dict[str, str]:
        """Provides AI-assisted barrier suggestions requiring human validation."""
        client = cls.get_client()
        if not client:
            return {
                "detected_category": "Unclassified Barrier",
                "notes": "Offline heuristic: Visual inspection required. Please select barrier type manually.",
                "human_confirmation_needed": "true"
            }
        try:
            prompt = (
                "Analyze this urban accessibility barrier. Identify if there are stairs, missing curb ramps, "
                "broken pavement, steep slopes, or construction. Format output strictly as: "
                "Category: <category>; Observation: <concise summary>"
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, image]
            )
            return {
                "detected_category": "Suggested: Barrier Detected",
                "notes": response.text.strip(),
                "human_confirmation_needed": "true"
            }
        except Exception as exc:
            return {
                "detected_category": "Review Needed",
                "notes": f"Automated inspection failed ({exc}).",
                "human_confirmation_needed": "true"
            }
