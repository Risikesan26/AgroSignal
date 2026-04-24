# Google AI Studio — Function Declarations

Use these in **AI Studio → Create Prompt → Tools → Function Calling**.

---

## How to Set Up

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click **"Create Prompt"** (or open an existing one)
3. Select model: **Gemini 1.5 Flash** or **Gemini 2.0 Flash**
4. In the left sidebar, click **"Tools"**
5. Under **"Code Execution"** / **"Function Calling"**, enable **Function Calling**
6. Click **"Add Function"** for each tool below
7. Paste the **Name**, **Description**, and **Parameters** for each one

---

## Tool 1: analyze_crop

**Name:** `analyze_crop`

**Description:**
```
Analyze crop market data using real FAMA (Federal Agricultural Marketing Authority) price records. Finds the best Malaysian state/region for selling a crop. Returns market price, local price, transport cost, net profit, and scores for all states. Always call this FIRST when a farmer asks where to sell.
```

**Parameters (JSON Schema):**
```json
{
  "type": "object",
  "properties": {
    "crop": {
      "type": "string",
      "description": "Crop name. Must be one of: Durian, Chili / Cili, Banana / Pisang, Tomato, Cabbage / Kubis, Spinach / Bayam",
      "enum": ["Durian", "Chili / Cili", "Banana / Pisang", "Tomato", "Cabbage / Kubis", "Spinach / Bayam"]
    },
    "quantity": {
      "type": "number",
      "description": "Quantity of crop in kilograms (kg)"
    },
    "timing": {
      "type": "string",
      "description": "When the harvest will be ready",
      "enum": ["within 1 week", "2-3 weeks", "1 month+", "already harvested"]
    },
    "state": {
      "type": "string",
      "description": "Farmer's current state in Malaysia",
      "enum": ["Perlis", "Kedah", "Penang", "Perak", "Selangor", "Kuala Lumpur", "Negeri Sembilan", "Melaka", "Johor", "Pahang", "Terengganu", "Kelantan", "Sabah", "Sarawak"]
    },
    "transport": {
      "type": "string",
      "description": "Transport method available to the farmer",
      "enum": ["own lorry", "hired truck", "motorbike only", "no transport"]
    }
  },
  "required": ["crop", "quantity", "timing", "state", "transport"]
}
```

---

## Tool 2: generate_plan

**Name:** `generate_plan`

**Description:**
```
Generate a complete AI-powered selling plan for a farmer. Combines FAMA market model data with narrative analysis. Returns: action steps, best days to sell, before/after profit comparison, market analysis, and all numbers needed for a selling plan. Call this when the farmer wants a detailed plan or strategy.
```

**Parameters (JSON Schema):**
```json
{
  "type": "object",
  "properties": {
    "crop": {
      "type": "string",
      "description": "Crop name",
      "enum": ["Durian", "Chili / Cili", "Banana / Pisang", "Tomato", "Cabbage / Kubis", "Spinach / Bayam"]
    },
    "quantity": {
      "type": "number",
      "description": "Quantity in kg"
    },
    "timing": {
      "type": "string",
      "description": "Harvest timing",
      "enum": ["within 1 week", "2-3 weeks", "1 month+", "already harvested"]
    },
    "state": {
      "type": "string",
      "description": "Farmer's state in Malaysia",
      "enum": ["Perlis", "Kedah", "Penang", "Perak", "Selangor", "Kuala Lumpur", "Negeri Sembilan", "Melaka", "Johor", "Pahang", "Terengganu", "Kelantan", "Sabah", "Sarawak"]
    },
    "transport": {
      "type": "string",
      "description": "Transport type",
      "enum": ["own lorry", "hired truck", "motorbike only", "no transport"],
      "default": "own lorry"
    }
  },
  "required": ["crop", "quantity", "timing", "state"]
}
```

---

## Tool 3: explain_recommendation

**Name:** `explain_recommendation`

**Description:**
```
Explain WHY a specific market region was recommended for a farmer. Provides a farmer-friendly explanation covering demand/supply dynamics, price advantage, transport feasibility, and seasonal factors. Call this when the farmer asks "why?" or wants to understand the reasoning.
```

**Parameters (JSON Schema):**
```json
{
  "type": "object",
  "properties": {
    "crop": {
      "type": "string",
      "description": "Crop name"
    },
    "state": {
      "type": "string",
      "description": "Farmer's state"
    },
    "bestRegion": {
      "type": "string",
      "description": "The recommended selling region"
    },
    "marketPrice": {
      "type": "number",
      "description": "Market price in RM per kg"
    },
    "localPrice": {
      "type": "number",
      "description": "Local price in RM per kg"
    },
    "profitGain": {
      "type": "number",
      "description": "Total profit gain in RM"
    }
  },
  "required": ["crop", "state", "bestRegion", "marketPrice", "localPrice", "profitGain"]
}
```

---

## Tool 4: weather_impact

**Name:** `weather_impact`

**Description:**
```
Assess weather and seasonal impact on a crop in a given Malaysian state. Returns peak/off-peak months, monsoon risk level, whether current month is risky, and timing advice. Call this when the farmer asks about weather, monsoon, seasonal risks, or best time to harvest.
```

**Parameters (JSON Schema):**
```json
{
  "type": "object",
  "properties": {
    "state": {
      "type": "string",
      "description": "Malaysian state",
      "enum": ["Perlis", "Kedah", "Penang", "Perak", "Selangor", "Kuala Lumpur", "Negeri Sembilan", "Melaka", "Johor", "Pahang", "Terengganu", "Kelantan", "Sabah", "Sarawak"]
    },
    "crop": {
      "type": "string",
      "description": "Crop name",
      "enum": ["Durian", "Chili / Cili", "Banana / Pisang", "Tomato", "Cabbage / Kubis", "Spinach / Bayam"]
    }
  },
  "required": ["state", "crop"]
}
```

---

## System Instruction (paste into "System Instructions" box)

```
You are AgroSignal Agent — an AI-powered agricultural market advisor for Malaysian farmers.

RULES:
1. ALWAYS call analyze_crop first when a farmer asks where to sell
2. Use generate_plan when they want a full selling strategy
3. Use explain_recommendation when they ask "why this market?"
4. Use weather_impact when weather/timing/monsoon is mentioned
5. Never guess prices — always use tool results
6. All prices are in Malaysian Ringgit (RM)
7. Respond in the farmer's language (English or Bahasa Melayu)
8. Present results in a clear, structured format with emojis

RESPONSE FORMAT after calling analyze_crop:
📊 Market Analysis for [Crop]
🏆 Best Region: [Region]
💰 Market Price: RM [X]/kg (vs RM [Y]/kg locally)
📈 Profit Gain: +RM [Z]
🚛 Transport Cost: RM [C]
✅ Net Profit: RM [N]

Then give a 1-2 sentence action recommendation.
```

---

## Test Prompts

Try these in the chat:
1. `I have 500kg of banana in Selangor, where should I sell?`
2. `Why is Johor the best market?`
3. `What's the weather risk for durian in Pahang?`
4. `Give me a full selling plan for 300kg of chili from Kedah`
