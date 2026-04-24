# ══════════════════════════════════════════════════════════════════
#  AgroSignal — main.py
#  FastAPI backend: data loading, recommendation engine, API routes
# ══════════════════════════════════════════════════════════════════

import os
import json
import logging
import re
import numpy as np
import pandas as pd
import httpx
from typing import Optional
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ──────────────────────────────────────────
# 0. LOGGING
# ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("agrosignal")

# ──────────────────────────────────────────
# 1. ENV
# ──────────────────────────────────────────
load_dotenv()

CSV_PATH        = os.getenv("FAMA_CSV_PATH",       "./data/fama_prices.csv")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY",       "")
GMAPS_API_KEY   = os.getenv("GOOGLE_MAPS_API_KEY",  "")

# ──────────────────────────────────────────
# 2. CROP NORMALISATION MAP
#    UI label  →  FAMA komoditi value
# ──────────────────────────────────────────
CROP_MAP: dict[str, str] = {
    # exact FAMA values (lowercase)
    "durian":      "durian",
    "cili hijau":  "cili hijau",
    "pisang mas":  "pisang mas",
    "tomato":      "tomato",
    "bayam":       "bayam",
    "kubis bulat": "kubis bulat",
    # UI display labels
    "Durian":                "durian",
    "Chili / Cili":          "cili hijau",
    "Banana / Pisang":       "pisang mas",
    "Tomato":                "tomato",
    "Cabbage / Kubis":       "kubis bulat",
    "Spinach / Bayam":       "bayam",
}

# ──────────────────────────────────────────
# 3. DISTANCE MATRIX  (km, road estimate)
#    All 16 Malaysian states/territories
# ──────────────────────────────────────────
DISTANCES: dict[tuple[str, str], int] = {
    # Selangor as hub
    ("selangor", "kuala lumpur"):       30,
    ("selangor", "negeri sembilan"):    70,
    ("selangor", "melaka"):            140,
    ("selangor", "johor"):             350,
    ("selangor", "perak"):             250,
    ("selangor", "pahang"):            200,
    ("selangor", "terengganu"):        380,
    ("selangor", "kelantan"):          450,
    ("selangor", "penang"):            400,
    ("selangor", "kedah"):             470,
    ("selangor", "perlis"):            520,
    ("selangor", "sabah"):            1600,
    ("selangor", "sarawak"):          1400,
    ("selangor", "w.p. labuan"):      1700,
    # Johor
    ("johor", "melaka"):               130,
    ("johor", "negeri sembilan"):      210,
    ("johor", "pahang"):               250,
    ("johor", "perak"):                500,
    ("johor", "penang"):               650,
    ("johor", "kelantan"):             550,
    ("johor", "terengganu"):           470,
    ("johor", "sabah"):               1800,
    ("johor", "sarawak"):             1600,
    ("johor", "w.p. labuan"):         1900,
    # Perak
    ("perak", "penang"):               150,
    ("perak", "kedah"):                100,
    ("perak", "pahang"):               200,
    ("perak", "kelantan"):             280,
    ("perak", "perlis"):               190,
    # Penang
    ("penang", "kedah"):                70,
    ("penang", "perlis"):               90,
    ("penang", "kelantan"):            350,
    # East Malaysia (sea + road estimates)
    ("sabah", "sarawak"):              700,
    ("sabah", "w.p. labuan"):          120,
    ("sarawak", "w.p. labuan"):        500,
    # Close neighbours
    ("kuala lumpur", "negeri sembilan"): 65,
    ("kuala lumpur", "melaka"):         145,
    ("negeri sembilan", "melaka"):       80,
    ("pahang", "terengganu"):           190,
    ("pahang", "kelantan"):             220,
    ("terengganu", "kelantan"):          90,
    ("kedah", "perlis"):                 50,
}

# ──────────────────────────────────────────
# 4. TRANSPORT COST RATES  (RM / kg / km)
# ──────────────────────────────────────────
TRANSPORT_RATES: dict[str, float] = {
    "own lorry":      0.015,   # cheapest — no hire fee
    "hired truck":    0.025,   # includes hire cost
    "motorbike only": 0.040,   # small loads, high per-unit cost
    "no transport":   0.000,   # buyer collects — no cost to farmer
}


from google.cloud import discoveryengine_v1 as discoveryengine

def search_fama(query: str) -> str:
    client = discoveryengine.SearchServiceClient()
    request = discoveryengine.SearchRequest(
        serving_config=f"projects/agrosignal-494017/locations/global/collections/default_collection/engines/agrosignaldata_1777006287953/servingConfigs/default_config",
        query=query,
        page_size=5,
    )
    response = client.search(request)
    return "\n".join([r.document.derived_struct_data for r in response.results])

# ──────────────────────────────────────────
# 5. GLOBAL MODEL STATE  (populated at startup)
# ──────────────────────────────────────────
_model: pd.DataFrame | None = None


def _build_model(df: pd.DataFrame) -> pd.DataFrame:
    """Reproduce the notebook scoring pipeline and return the model DataFrame."""

    # ── 5a. Normalise komoditi ──
    def normalise(x: str) -> str | None:
        x = x.strip().lower()
        for key in ["cili hijau", "kubis bulat", "pisang mas",
                    "durian", "tomato", "bayam"]:
            if key in x:
                return key
        return None

    df = df.copy()
    df["Komoditi"] = df["Komoditi"].astype(str).apply(normalise)
    df = df[df["Komoditi"].notna()].copy()
    df = df.sort_values(["Komoditi", "Negeri", "Tarikh"])

    # ── 5b. Price score (normalised per crop) ──
    price_table = (
        df.groupby(["Komoditi", "Negeri"])["Harga (RM)"]
        .mean()
        .reset_index()
    )
    price_table["price_score"] = price_table.groupby("Komoditi")["Harga (RM)"].transform(
        lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else 0.5
    )

    # ── 5c. Demand score (direction of price change) ──
    df["Perubahan"] = df.groupby(["Komoditi", "Negeri"])["Harga (RM)"].diff()
    trend = df.groupby(["Komoditi", "Negeri"])["Perubahan"].mean().reset_index()
    trend["demand_score"] = trend["Perubahan"].apply(
        lambda x: 1.0 if x > 0 else (0.5 if x == 0 else 0.0)
    )

    # ── 5d. Stability score (inverse normalised std) ──
    volatility = df.groupby(["Komoditi", "Negeri"])["Harga (RM)"].std().reset_index()
    volatility["stability_score"] = 1 - volatility.groupby("Komoditi")["Harga (RM)"].transform(
        lambda x: (x - x.min()) / (x.max() - x.min()) if x.max() != x.min() else 0.5
    )

    # ── 5e. Merge & final score ──
    model = price_table.merge(trend, on=["Komoditi", "Negeri"])
    model = model.merge(volatility, on=["Komoditi", "Negeri"])
    model["final_score"] = (
        0.5 * model["price_score"] +
        0.3 * model["demand_score"] +
        0.2 * model["stability_score"]
    )

    log.info("Model built — %d crop/state combinations", len(model))
    return model


# ──────────────────────────────────────────
# 6. HELPER FUNCTIONS
# ──────────────────────────────────────────

def get_distance(from_state: str, to_state: str) -> int:
    """Return road distance in km between two states (case-insensitive)."""
    a, b = from_state.strip().lower(), to_state.strip().lower()
    if a == b:
        return 0
    dist = DISTANCES.get((a, b)) or DISTANCES.get((b, a))
    if dist is None:
        log.warning("No distance entry for (%s, %s) — defaulting to 300 km", a, b)
        return 300
    return dist


def calc_transport_cost(distance: int, quantity: float, transport_type: str) -> float:
    """Return total transport cost in RM."""
    rate = TRANSPORT_RATES.get(transport_type.lower(), 0.02)
    return round(distance * quantity * rate, 2)


def cadangan_net_profit(
    komoditi: str,
    kuantiti: float,
    negeri_asal: str,
    transport_type: str = "own lorry",
) -> dict:
    """
    Find the state that maximises net profit after transport cost.

    Returns a dict with keys:
        negeri, harga, distance, transport_cost, net_profit, score
    """
    if _model is None:
        raise RuntimeError("Model not initialised. Check startup logs.")

    data = _model[_model["Komoditi"] == komoditi].copy()
    if data.empty:
        raise ValueError(f"No data found for crop: '{komoditi}'")

    results = []
    for _, row in data.iterrows():
        negeri_target = row["Negeri"]
        # price column is 'Harga (RM)_x' after merging
        harga_col = "Harga (RM)_x" if "Harga (RM)_x" in row.index else "Harga (RM)"
        harga = float(row[harga_col])

        dist     = get_distance(negeri_asal, negeri_target)
        kos      = calc_transport_cost(dist, kuantiti, transport_type)
        revenue  = harga * kuantiti
        net      = revenue - kos

        results.append({
            "negeri":         negeri_target,
            "harga":          round(harga, 2),
            "distance":       dist,
            "transport_cost": kos,
            "net_profit":     round(net, 2),
            "score":          round(float(row["final_score"]), 4),
        })

    result_df = pd.DataFrame(results)

    # ── also attach the worst state for profit-gap calculation ──
    best    = result_df.sort_values("net_profit", ascending=False).iloc[0].to_dict()
    worst   = result_df.sort_values("net_profit", ascending=True).iloc[0].to_dict()
    local   = result_df[
        result_df["negeri"].str.lower() == negeri_asal.lower()
    ]
    local_price = float(local["harga"].values[0]) if not local.empty else worst["harga"]
    local_revenue = round(local_price * kuantiti, 2)

    best["local_price"]   = round(local_price, 2)
    best["local_revenue"] = local_revenue
    best["total_revenue"] = round(best["harga"] * kuantiti, 2)
    best["profit_gain"]   = round((best["harga"] - local_price) * kuantiti, 2)
    best["all_states"]    = result_df.to_dict("records")   # for demand map

    return best


# ──────────────────────────────────────────
# 7. STARTUP / SHUTDOWN
# ──────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load data and build model before the server starts accepting requests."""
    global _model

    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(
            f"FAMA data not found at: {CSV_PATH}\n"
            "Set FAMA_CSV_PATH in your .env file."
        )

    log.info("Loading FAMA data from: %s", CSV_PATH)
    raw_df = pd.read_csv(CSV_PATH)
    log.info("Loaded %d raw rows", len(raw_df))

    _model = _build_model(raw_df)
    log.info("✅ AgroSignal backend ready")

    yield  # ← server runs here

    log.info("Shutting down AgroSignal backend")


# ──────────────────────────────────────────
# 8. FASTAPI APP
# ──────────────────────────────────────────

app = FastAPI(
    title="AgroSignal API",
    description="FAMA-powered crop market recommendation engine for Malaysian farmers",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # tighten to your domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Agent Orchestrator ──
from agent import router as agent_router
app.include_router(agent_router)

# ──────────────────────────────────────────
# 9. REQUEST / RESPONSE SCHEMAS
# ──────────────────────────────────────────

class FarmerInput(BaseModel):
    crop:      str   = Field(..., example="Chili / Cili")
    quantity:  float = Field(..., gt=0, example=500)
    timing:    str   = Field(..., example="within 1 week")
    state:     str   = Field(..., example="Selangor")
    transport: str   = Field(..., example="own lorry")


class RecommendationResult(BaseModel):
    # ── core numbers (computed from real FAMA data) ──
    bestRegion:             str
    estimatedMarketPrice:   float
    estimatedLocalPrice:    float
    totalRevenue:           float
    localRevenue:           float
    profitGainPerKg:        float
    totalProfitGain:        float
    distanceKm:             int
    transportCostRM:        float
    netProfitAfterTransport: float
    finalScore:             float
    # ── demand map for all states ──
    allStates:              list[dict]


# ──────────────────────────────────────────
# 10. ROUTES
# ──────────────────────────────────────────

@app.get("/api/key")
def get_key():
    """Return the Gemini API key to the frontend (served from same origin)."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set in environment")
    return {"key": GEMINI_API_KEY}


@app.get("/api/maps-key")
def get_maps_key():
    """Return the Google Maps API key to the frontend."""
    if not GMAPS_API_KEY:
        raise HTTPException(status_code=500, detail="GOOGLE_MAPS_API_KEY not set in environment")
    return {"key": GMAPS_API_KEY}


@app.post("/api/analyze", response_model=RecommendationResult)
def analyze(data: FarmerInput):
    """
    Core recommendation endpoint.
    Receives farmer inputs, runs the FAMA scoring model,
    and returns real computed numbers for the frontend to use.
    """
    # ── map UI crop label → FAMA komoditi ──
    komoditi = CROP_MAP.get(data.crop)
    if komoditi is None:
        raise HTTPException(
            status_code=400,
            detail=f"Crop '{data.crop}' is not yet in the FAMA dataset. "
                   "Available: durian, cili hijau, pisang mas, tomato, bayam, kubis bulat",
        )

    try:
        result = cadangan_net_profit(
            komoditi=komoditi,
            kuantiti=data.quantity,
            negeri_asal=data.state,
            transport_type=data.transport,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    profit_per_kg = round(result["harga"] - result["local_price"], 2)

    return RecommendationResult(
        bestRegion              = result["negeri"],
        estimatedMarketPrice    = result["harga"],
        estimatedLocalPrice     = result["local_price"],
        totalRevenue            = result["total_revenue"],
        localRevenue            = result["local_revenue"],
        profitGainPerKg         = profit_per_kg,
        totalProfitGain         = result["profit_gain"],
        distanceKm              = result["distance"],
        transportCostRM         = result["transport_cost"],
        netProfitAfterTransport = result["net_profit"],
        finalScore              = result["score"],
        allStates               = result["all_states"],
    )


@app.get("/api/crops")
def list_crops():
    """Return the list of crops that have data in the current dataset."""
    available = [k for k, v in CROP_MAP.items() if v is not None and "/" not in k]
    return {"crops": available}


@app.get("/api/health")
def health():
    """Liveness check — confirm model is loaded."""
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {
        "status":        "ok",
        "rows_in_model": len(_model),
        "crops":         _model["Komoditi"].unique().tolist(),
    }


# ──────────────────────────────────────────
# 11. GEMINI SERVER-SIDE HELPER
# ──────────────────────────────────────────

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-1.5-flash:generateContent"
)


async def call_gemini(prompt: str) -> str:
    """Call Gemini API server-side and return the text response."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4000},
            },
        )
    if resp.status_code != 200:
        detail = resp.json().get("error", {}).get("message", resp.text)
        raise HTTPException(status_code=502, detail=f"Gemini error: {detail}")

    data = resp.json()
    return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")


def parse_gemini_json(raw: str) -> dict:
    """Extract and parse the first JSON object from Gemini's response."""
    cleaned = re.sub(r"```json|```", "", raw).strip()
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        raise HTTPException(status_code=502, detail="Could not parse Gemini JSON response")
    return json.loads(match.group(0))


# ──────────────────────────────────────────
# 12. VERTEX AI AGENT BUILDER TOOL ENDPOINTS
# ──────────────────────────────────────────

# ── Schemas ──

class GeneratePlanInput(BaseModel):
    crop:      str   = Field(..., description="Crop name, e.g. 'Banana / Pisang'", example="Banana / Pisang")
    quantity:  float = Field(..., gt=0, description="Quantity in kg", example=500)
    timing:    str   = Field(..., description="Harvest timing", example="within 1 week")
    state:     str   = Field(..., description="Farmer's state", example="Selangor")
    transport: str   = Field("own lorry", description="Transport type", example="own lorry")


class ExplainInput(BaseModel):
    crop:        str   = Field(..., description="Crop name", example="Banana / Pisang")
    state:       str   = Field(..., description="Farmer's state", example="Selangor")
    bestRegion:  str   = Field(..., description="Recommended selling region", example="Johor")
    marketPrice: float = Field(..., description="Market price RM/kg", example=4.50)
    localPrice:  float = Field(..., description="Local price RM/kg", example=3.20)
    profitGain:  float = Field(..., description="Total profit gain RM", example=650)


class WeatherInput(BaseModel):
    state: str = Field(..., description="Malaysian state", example="Selangor")
    crop:  str = Field(..., description="Crop name", example="Banana / Pisang")


# ── Tool 2: Generate Plan ──

@app.post("/api/action/generate-plan")
async def generate_plan(data: GeneratePlanInput):
    """
    AGENT TOOL: Generate a complete AI-powered selling plan.

    1. Runs the FAMA scoring model to get real market numbers.
    2. Calls Gemini server-side to generate narrative (action plan, best days,
       before/after comparison, full analysis).
    3. Returns everything the agent (or PDF) needs in one response.
    """
    # ── Step 1: Run FAMA model ──
    komoditi = CROP_MAP.get(data.crop)
    if komoditi is None:
        raise HTTPException(
            status_code=400,
            detail=f"Crop '{data.crop}' is not in the FAMA dataset. "
                   f"Available: {', '.join(set(CROP_MAP.values()))}",
        )

    try:
        result = cadangan_net_profit(
            komoditi=komoditi,
            kuantiti=data.quantity,
            negeri_asal=data.state,
            transport_type=data.transport,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    best_region       = result["negeri"]
    market_price      = result["harga"]
    local_price       = result["local_price"]
    total_profit_gain = result["profit_gain"]
    total_revenue     = result["total_revenue"]
    local_revenue     = result["local_revenue"]
    transport_cost    = result["transport_cost"]
    net_profit        = result["net_profit"]
    distance_km       = result["distance"]
    travel_hours      = round(distance_km / 80, 1)

    # ── Step 2: Call Gemini for narrative ──
    prompt = f"""You are AgroSignal, an AI market advisor for Malaysian farmers.
The following data was computed from REAL FAMA price records — do NOT change any numbers.

REAL DATA (from model):
- Crop: {data.crop}
- Quantity: {data.quantity} kg
- Farmer's State: {data.state}
- Harvest Timing: {data.timing}
- Transport: {data.transport}
- Best Region to Sell: {best_region}
- Market Price (FAMA): RM {market_price}/kg
- Local Price (estimated): RM {local_price}/kg
- Total Profit Gain: RM {total_profit_gain}
- Transport Cost: RM {transport_cost}
- Net Profit After Transport: RM {net_profit}
- Distance: {distance_km} km
- Travel Time: ~{travel_hours} hrs

Return ONLY a valid JSON object (no markdown, no text outside JSON):

{{
  "bestMarketCity": "specific city/town in {best_region}",
  "demandLevel": "High",
  "bestDays": ["Wed", "Thu", "Fri"],
  "goodDays": ["Mon", "Tue"],
  "actionText": "1 sentence telling farmer exactly what to do",
  "actionSub": "1 sentence on why the timing is right",
  "shortReason": "2-3 sentences explaining why {best_region} is best for {data.crop} right now.",
  "reasonChips": ["High demand", "Low supply", "Active buyers", "Good logistics"],
  "beforePoints": [
    "Sells to nearest local market without comparing prices",
    "Receives only RM {local_price}/kg at local market",
    "Misses seasonal demand peaks in higher-value regions",
    "No visibility into supply/demand across other states"
  ],
  "afterPoints": [
    "Directed to {best_region} — highest demand for {data.crop}",
    "Earns RM {market_price}/kg vs RM {local_price}/kg locally",
    "Timed for peak market window based on FAMA data",
    "Net gain of RM {net_profit} after transport costs"
  ],
  "fullAnalysis": "3 sentences explaining the market opportunity."
}}

Return ONLY the JSON object."""

    raw_text = await call_gemini(prompt)
    narrative = parse_gemini_json(raw_text)

    # ── Step 3: Merge model data + narrative ──
    plan = {
        # Real numbers from FAMA model
        "bestRegion":              best_region,
        "estimatedMarketPrice":    market_price,
        "estimatedLocalPrice":     local_price,
        "totalProfitGain":         total_profit_gain,
        "totalRevenue":            total_revenue,
        "localRevenue":            local_revenue,
        "transportCostRM":         transport_cost,
        "netProfitAfterTransport": net_profit,
        "distanceKm":              distance_km,
        "travelHours":             travel_hours,
        "finalScore":              result["score"],
        # Narrative from Gemini
        **narrative,
        # Input echo (useful for agent context)
        "input": {
            "crop":      data.crop,
            "quantity":  data.quantity,
            "timing":    data.timing,
            "state":     data.state,
            "transport": data.transport,
        },
    }

    log.info("Generated plan: %s → %s (RM %.2f gain)", data.crop, best_region, total_profit_gain)
    return JSONResponse(content=plan)


# ── Tool 3: Explain Recommendation ──

@app.post("/api/action/explain-recommendation")
async def explain_recommendation(data: ExplainInput):
    """
    AGENT TOOL: Explain why a specific market recommendation was made.

    Uses Gemini to produce a farmer-friendly, natural-language explanation
    of the recommendation, suitable for chat-based interaction.
    """
    prompt = f"""You are AgroSignal, an AI advisor for Malaysian farmers.

A farmer in {data.state} growing {data.crop} was recommended to sell in {data.bestRegion}.
The market price is RM {data.marketPrice}/kg vs RM {data.localPrice}/kg locally.
Total profit gain is RM {data.profitGain}.

Write a clear, friendly explanation in 4-5 sentences for why {data.bestRegion} is the
best market. Cover: demand/supply dynamics, price advantage, transport feasibility,
and seasonal factors. Use simple language a farmer would understand.

Return ONLY a JSON object:
{{
  "explanation": "your explanation here",
  "keyFactors": ["factor 1", "factor 2", "factor 3"],
  "riskNotes": "1 sentence about any risks or considerations",
  "confidence": "high"
}}"""

    raw_text = await call_gemini(prompt)
    result = parse_gemini_json(raw_text)

    return JSONResponse(content=result)


# ── Tool 4: Weather Impact (seasonal estimation) ──

# Seasonal crop data for Malaysia (curated reference data)
SEASONAL_DATA: dict[str, dict] = {
    "durian":     {"peak": ["Jun", "Jul", "Aug"], "offpeak": ["Jan", "Feb", "Mar"],
                   "riskMonths": ["Nov", "Dec"], "notes": "Durian season peaks mid-year. Heavy rain in Nov-Dec can damage fruit."},
    "cili hijau": {"peak": ["Mar", "Apr", "May"], "offpeak": ["Sep", "Oct"],
                   "riskMonths": ["Nov", "Dec"], "notes": "Chili supply drops during monsoon, driving prices up."},
    "pisang mas": {"peak": ["Year-round"], "offpeak": [],
                   "riskMonths": ["Nov", "Dec"], "notes": "Bananas fruit year-round but heavy rains cause waterlogging."},
    "tomato":     {"peak": ["Apr", "May", "Jun"], "offpeak": ["Nov", "Dec"],
                   "riskMonths": ["Nov", "Dec", "Jan"], "notes": "Highland tomatoes affected by monsoon rains."},
    "bayam":      {"peak": ["Year-round"], "offpeak": [],
                   "riskMonths": ["Nov", "Dec"], "notes": "Spinach grows fast but excess rain reduces quality."},
    "kubis bulat":{"peak": ["May", "Jun", "Jul"], "offpeak": ["Nov", "Dec"],
                   "riskMonths": ["Nov", "Dec"], "notes": "Cameron Highlands cabbage affected by heavy rain and landslides."},
}

# Regional monsoon risk
MONSOON_RISK: dict[str, str] = {
    "Kelantan":    "high",   "Terengganu":     "high",
    "Pahang":      "medium", "Johor":          "medium",
    "Selangor":    "low",    "Kuala Lumpur":   "low",
    "Perak":       "low",    "Kedah":          "medium",
    "Perlis":      "medium", "Penang":         "low",
    "Negeri Sembilan": "low","Melaka":         "low",
    "Sabah":       "medium", "Sarawak":        "medium",
    "W.P. Labuan": "medium",
}


@app.post("/api/weather-impact")
async def weather_impact(data: WeatherInput):
    """
    AGENT TOOL: Assess weather/seasonal impact on a crop in a given state.

    Returns seasonal risk assessment, best harvest windows,
    and monsoon exposure for the farmer's region.
    """
    komoditi = CROP_MAP.get(data.crop)
    if komoditi is None:
        raise HTTPException(
            status_code=400,
            detail=f"Crop '{data.crop}' not recognised.",
        )

    crop_season = SEASONAL_DATA.get(komoditi, {
        "peak": ["Unknown"], "offpeak": ["Unknown"],
        "riskMonths": [], "notes": "No seasonal data available for this crop.",
    })

    # Determine current month context
    from datetime import datetime
    current_month = datetime.now().strftime("%b")
    is_risk_month = current_month in crop_season.get("riskMonths", [])
    is_peak = current_month in crop_season.get("peak", [])

    monsoon_risk = MONSOON_RISK.get(data.state, "unknown")

    # Build timing advice
    if is_risk_month:
        timing_advice = (
            f"⚠ {current_month} is a high-risk month for {data.crop}. "
            "Consider delaying harvest or securing covered transport."
        )
    elif is_peak:
        timing_advice = (
            f"✅ {current_month} is peak season for {data.crop}. "
            "Prices may be lower due to high supply — sell quickly or target premium markets."
        )
    else:
        timing_advice = (
            f"📊 {current_month} is a normal period for {data.crop}. "
            "Standard market conditions expected."
        )

    result = {
        "crop":           data.crop,
        "state":          data.state,
        "currentMonth":   current_month,
        "peakMonths":     crop_season["peak"],
        "offPeakMonths":  crop_season["offpeak"],
        "riskMonths":     crop_season["riskMonths"],
        "seasonalNotes":  crop_season["notes"],
        "monsoonRisk":    monsoon_risk,
        "isRiskMonth":    is_risk_month,
        "isPeakSeason":   is_peak,
        "timingAdvice":   timing_advice,
    }

    log.info("Weather impact: %s in %s — risk=%s, peak=%s", data.crop, data.state, is_risk_month, is_peak)
    return JSONResponse(content=result)


# ──────────────────────────────────────────
# 11. SERVE FRONTEND  (must be last)
# ──────────────────────────────────────────

STATIC_DIR = os.getenv("STATIC_DIR", "./static")

if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    log.info("Serving frontend from: %s", STATIC_DIR)
else:
    log.warning(
        "Static directory '%s' not found — frontend will not be served. "
        "Set STATIC_DIR in .env or create the folder.",
        STATIC_DIR,
    )


# ──────────────────────────────────────────
# 12. DEV ENTRY POINT
# ──────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,     # auto-restart on file changes during development
    )
