# ══════════════════════════════════════════════════════════════════
#  AgroSignal Agent Orchestrator
# ══════════════════════════════════════════════════════════════════

import os
import json
import httpx
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ── ADK Agent import ──
try:
    from adk_agent import app as adk_app
    ADK_AVAILABLE = True
    print("✅ ADK Agent loaded successfully")
except Exception as e:
    ADK_AVAILABLE = False
    adk_app = None
    print(f"⚠ ADK Agent not available: {e} — will use Gemini fallback")

load_dotenv()
log = logging.getLogger("agrosignal.agent")

# ──────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-2.0-flash-exp"
GEMINI_URL     = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{GEMINI_MODEL}:generateContent"
)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ──────────────────────────────────────────
# TOOL DEFINITIONS
# ──────────────────────────────────────────
TOOL_DECLARATIONS = [
    {
        "function_declarations": [
            {
                "name": "analyze_crop",
                "description": (
                    "Analyze crop market data using real FAMA price records. "
                    "Finds the best Malaysian state/region for selling a crop. "
                    "Returns market price, local price, transport cost, net profit. "
                    "Always call this FIRST when a farmer asks where to sell."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "crop": {
                            "type": "string",
                            "description": "Crop name",
                            "enum": ["Durian", "Chili / Cili", "Banana / Pisang",
                                     "Tomato", "Cabbage / Kubis", "Spinach / Bayam"],
                        },
                        "quantity": {"type": "number", "description": "Quantity in kg"},
                        "timing": {
                            "type": "string",
                            "description": "Harvest timing",
                            "enum": ["within 1 week", "2-3 weeks", "1 month+", "already harvested"],
                        },
                        "state": {
                            "type": "string",
                            "description": "Farmer's state in Malaysia",
                            "enum": [
                                "Perlis", "Kedah", "Penang", "Perak", "Selangor",
                                "Kuala Lumpur", "Negeri Sembilan", "Melaka", "Johor",
                                "Pahang", "Terengganu", "Kelantan", "Sabah", "Sarawak",
                            ],
                        },
                        "transport": {
                            "type": "string",
                            "description": "Transport method",
                            "enum": ["own lorry", "hired truck", "motorbike only", "no transport"],
                        },
                    },
                    "required": ["crop", "quantity", "timing", "state", "transport"],
                },
            },
            {
                "name": "generate_plan",
                "description": (
                    "Generate a complete AI-powered selling plan. Combines FAMA model "
                    "data with narrative analysis. Returns action steps, best days, "
                    "profit comparison. Call when farmer wants a detailed plan."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "crop": {
                            "type": "string",
                            "enum": ["Durian", "Chili / Cili", "Banana / Pisang",
                                     "Tomato", "Cabbage / Kubis", "Spinach / Bayam"],
                        },
                        "quantity":  {"type": "number"},
                        "timing":    {"type": "string"},
                        "state":     {"type": "string"},
                        "transport": {"type": "string"},
                    },
                    "required": ["crop", "quantity", "timing", "state"],
                },
            },
            {
                "name": "explain_recommendation",
                "description": (
                    "Explain WHY a specific market was recommended. "
                    "Provides farmer-friendly explanation. Call when farmer asks why."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "crop":        {"type": "string"},
                        "state":       {"type": "string"},
                        "bestRegion":  {"type": "string"},
                        "marketPrice": {"type": "number"},
                        "localPrice":  {"type": "number"},
                        "profitGain":  {"type": "number"},
                    },
                    "required": ["crop", "state", "bestRegion",
                                 "marketPrice", "localPrice", "profitGain"],
                },
            },
        ]
    }
]

# ──────────────────────────────────────────
# SYSTEM INSTRUCTIONS
# ──────────────────────────────────────────
SYSTEM_INSTRUCTIONS = {
    "en": """You are AgroSignal Agent — an AI-powered agricultural market advisor for Malaysian farmers.

IMPORTANT: You MUST respond ONLY in English. Do not use Bahasa Melayu.

RULES:
1. ALWAYS call analyze_crop first when a farmer asks where to sell.
2. Use generate_plan when they want a full selling strategy.
3. Use explain_recommendation when they ask "why this market?"
4. Never guess prices — always use tool results.
5. All prices are in Malaysian Ringgit (RM).
6. If the farmer hasn't specified all required fields, ask them politely.

RESPONSE FORMAT after getting analyze_crop results:
📊 **Market Analysis for [Crop]**
🏆 Best Region: [Region]
💰 Market Price: RM [X]/kg (vs RM [Y]/kg locally)
📈 Profit Gain: +RM [Z]
🚛 Transport Cost: RM [C]
✅ Net Profit: RM [N]

Then give a 1-2 sentence action recommendation.""",

    "bm": """Anda adalah Agen AgroSignal — penasihat pasaran pertanian berkuasa AI untuk petani Malaysia.

PENTING: Anda MESTI menjawab HANYA dalam Bahasa Melayu. Jangan gunakan bahasa Inggeris.

PERATURAN:
1. SENTIASA panggil analyze_crop dahulu apabila petani bertanya di mana hendak menjual.
2. Gunakan generate_plan apabila mereka mahukan strategi jualan penuh.
3. Gunakan explain_recommendation apabila mereka bertanya "kenapa pasaran ini?"
4. Jangan meneka harga — sentiasa gunakan hasil alat.
5. Semua harga dalam Ringgit Malaysia (RM).
6. Jika petani belum nyatakan semua maklumat, tanya dengan sopan.

FORMAT JAWAPAN selepas mendapat keputusan analyze_crop:
📊 **Analisis Pasaran untuk [Tanaman]**
🏆 Kawasan Terbaik: [Kawasan]
💰 Harga Pasaran: RM [X]/kg (vs RM [Y]/kg tempatan)
📈 Keuntungan: +RM [Z]
🚛 Kos Pengangkutan: RM [C]
✅ Untung Bersih: RM [N]

Kemudian beri cadangan tindakan 1-2 ayat."""
}

# ──────────────────────────────────────────
# TOOL → BACKEND ENDPOINT MAP
# ──────────────────────────────────────────
TOOL_ENDPOINTS = {
    "analyze_crop":           ("POST", "/api/analyze"),
    "generate_plan":          ("POST", "/api/action/generate-plan"),
    "explain_recommendation": ("POST", "/api/action/explain-recommendation"),
}


# ──────────────────────────────────────────
# ADK AGENT CALLER
# ──────────────────────────────────────────
async def call_adk_agent(message: str, session_id: str) -> str:
    """Call the ADK multi-agent system (Vertex AI Search grounded)."""
    if not ADK_AVAILABLE or adk_app is None:
        return None

    try:
        full_response = ""

        async for chunk in adk_app.stream_query(
            query=message,
            user_id=session_id,
        ):
            if hasattr(chunk, 'text'):
                full_response += chunk.text
            elif isinstance(chunk, dict):
                content = chunk.get('content', {})
                parts   = content.get('parts', [])
                for part in parts:
                    full_response += part.get('text', '')

        log.info("✅ ADK Agent responded (%d chars)", len(full_response))
        return full_response if full_response else None

    except Exception as e:
        log.warning("❌ ADK Agent error: %s", str(e))
        return None


# ──────────────────────────────────────────
# TOOL EXECUTOR
# ──────────────────────────────────────────
async def execute_tool(tool_name: str, args: dict) -> dict:
    """Execute a tool call against the backend API."""
    if tool_name not in TOOL_ENDPOINTS:
        return {"error": f"Unknown tool: {tool_name}"}

    method, path = TOOL_ENDPOINTS[tool_name]
    url = f"{BACKEND_URL}{path}"

    log.info("🔧 Executing tool: %s → %s %s", tool_name, method, url)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "POST":
                resp = await client.post(url, json=args)
            else:
                resp = await client.get(url, params=args)

        if resp.status_code != 200:
            return {"error": f"Backend returned {resp.status_code}: {resp.text}"}

        result = resp.json()
        log.info("   ✅ Tool result received (%d keys)", len(result))
        return result

    except Exception as e:
        log.error("   ❌ Tool execution failed: %s", str(e))
        return {"error": str(e)}


# ──────────────────────────────────────────
# GEMINI FALLBACK WITH TOOLS
# ──────────────────────────────────────────
async def call_gemini_with_tools(contents: list, language: str = "en", max_turns: int = 5) -> str:
    """Fallback: direct Gemini with function calling tools."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    for turn in range(max_turns):
        log.info("🔄 Gemini loop — turn %d/%d", turn + 1, max_turns)

        payload = {
            "contents": contents,
            "tools": TOOL_DECLARATIONS,
            "system_instruction": {
                "parts": [{"text": SYSTEM_INSTRUCTIONS.get(language, SYSTEM_INSTRUCTIONS["en"])}]
            },
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 4000,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json=payload,
            )

        if resp.status_code != 200:
            detail = resp.json().get("error", {}).get("message", resp.text)
            raise HTTPException(status_code=502, detail=f"Gemini error: {detail}")

        data      = resp.json()
        candidate = data.get("candidates", [{}])[0]
        content   = candidate.get("content", {})
        parts     = content.get("parts", [])

        function_calls = [p for p in parts if "functionCall" in p]

        if function_calls:
            contents.append(content)
            function_responses = []

            for fc_part in function_calls:
                fc        = fc_part["functionCall"]
                tool_name = fc["name"]
                tool_args = fc.get("args", {})
                result    = await execute_tool(tool_name, tool_args)

                function_responses.append({
                    "functionResponse": {
                        "name": tool_name,
                        "response": result,
                    }
                })

            contents.append({
                "role": "function",
                "parts": function_responses,
            })

            log.info("   📤 Fed %d tool result(s) back to Gemini", len(function_responses))

        else:
            text = "".join(p.get("text", "") for p in parts)
            log.info("✅ Gemini responded (%d chars)", len(text))
            return text

    return "I apologize, but I couldn't complete the analysis. Please try again."


# ══════════════════════════════════════════
# FASTAPI ROUTER
# ══════════════════════════════════════════

router = APIRouter(prefix="/api/agent", tags=["Agent"])


class ChatRequest(BaseModel):
    message:    str  = Field(..., description="Farmer's message",
                             example="I have 500kg of banana in Selangor")
    history:    list = Field(default=[], description="Conversation history")
    language:   str  = Field(default="en", description="'en' or 'bm'")
    session_id: str  = Field(default="default-session", description="Session ID")


class ChatResponse(BaseModel):
    reply:   str  = Field(..., description="Agent's response")
    history: list = Field(..., description="Updated conversation history")


@router.post("/chat", response_model=ChatResponse)
async def agent_chat(req: ChatRequest):
    """
    AgroSignal Agent Chat
    1. Tries ADK multi-agent (Vertex AI Search grounded) first
    2. Falls back to direct Gemini + tools if ADK unavailable
    """
    contents = list(req.history) if req.history else []
    contents.append({
        "role": "user",
        "parts": [{"text": req.message}],
    })

    reply = None

    # ── 1. Try ADK Agent (Vertex AI grounded) ──
    if ADK_AVAILABLE:
        log.info("🤖 Trying ADK multi-agent...")
        reply = await call_adk_agent(
            message=req.message,
            session_id=req.session_id
        )

    # ── 2. Fallback to direct Gemini with tools ──
    if not reply:
        log.info("⚡ Using Gemini fallback...")
        reply = await call_gemini_with_tools(
            contents=contents,
            language=req.language
        )

    updated_history = contents + [{
        "role": "model",
        "parts": [{"text": reply}],
    }]

    return ChatResponse(reply=reply, history=updated_history)
