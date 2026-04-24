import vertexai
import os
from dotenv import load_dotenv
from typing import Any

from google.adk.agents import llm_agent
from google.adk.sessions import vertex_ai_session_service
try:
    from vertexai.agent_engines import AdkApp
except ImportError:
    try:
        from vertexai.preview.reasoning_engines import AdkApp
    except ImportError:
        # Fallback for older SDKs or localized ADK installs
        try:
            from google.adk.apps import App as AdkApp
        except ImportError:
            AdkApp = None

from google.adk.tools import agent_tool
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.adk.tools import url_context
from google.adk.tools import VertexAiSearchTool


load_dotenv()

vertexai.init(
    project=os.getenv("VERTEX_PROJECT_ID", "agrosignal-494017"),
    location=os.getenv("VERTEX_LOCATION", "us-central1"),
)
VertexAiSessionService = vertex_ai_session_service.VertexAiSessionService


class AgentClass:

  def __init__(self):
    self.app = None

  def session_service_builder(self):
    return VertexAiSessionService()

  def set_up(self):
    """Sets up the ADK application."""
    market_analyzer_agent_google_search_agent = llm_agent.LlmAgent(
      name='Market_Analyzer_Agent_google_search_agent',
      model='gemini-1.5-flash',
      description=(
          'Agent specialized in performing Google searches.'
      ),
      sub_agents=[],
      instruction='Use the GoogleSearchTool to find information on the web.',
      tools=[
        GoogleSearchTool()
      ],
    )
    market_analyzer_agent_url_context_agent = llm_agent.LlmAgent(
      name='Market_Analyzer_Agent_url_context_agent',
      model='gemini-1.5-flash',
      description=(
          'Agent specialized in fetching content from URLs.'
      ),
      sub_agents=[],
      instruction='Use the UrlContextTool to retrieve content from provided URLs.',
      tools=[
        url_context
      ],
    )
    market_analyzer_agent_vertex_ai_search_agent = llm_agent.LlmAgent(
      name='Market_Analyzer_Agent_vertex_ai_search_agent',
      model='gemini-1.5-flash',
      description=(
          'Agent specialized in performing Vertex AI Search.'
      ),
      sub_agents=[],
      instruction='Use the VertexAISearchTool to find information using Vertex AI Search.',
      tools=[
        VertexAiSearchTool(
          data_store_id='projects/583139806956/locations/global/collections/default_collection/dataStores/agrosignaldata_1777006287953'
        )
      ],
    )
    market_analyzer_agent = llm_agent.LlmAgent(
      name='market_analyzer_agent',
      model='gemini-1.5-flash',
      description=(
          'Agent that handles a specific task'
      ),
      sub_agents=[],
      instruction='You are a crop market analyzer for Malaysian farmers.\n\nWhen a farmer asks where to sell their crop:\n1. Search fama_market_data tool for price records\n   Query example: \"durian price Johor 2024\"\n2. Use the results to find the highest price region\n3. Return: best region, price per kg, profit estimate\n\nAlways base answers on real FAMA data — never guess.',
      tools=[
        agent_tool.AgentTool(agent=market_analyzer_agent_google_search_agent),
        agent_tool.AgentTool(agent=market_analyzer_agent_url_context_agent),
        agent_tool.AgentTool(agent=market_analyzer_agent_vertex_ai_search_agent)
      ],
    )
    plan_generator_agent_google_search_agent = llm_agent.LlmAgent(
      name='Plan_Generator_Agent_google_search_agent',
      model='gemini-1.5-flash',
      description=(
          'Agent specialized in performing Google searches.'
      ),
      sub_agents=[],
      instruction='Use the GoogleSearchTool to find information on the web.',
      tools=[
        GoogleSearchTool()
      ],
    )
    plan_generator_agent_url_context_agent = llm_agent.LlmAgent(
      name='Plan_Generator_Agent_url_context_agent',
      model='gemini-1.5-flash',
      description=(
          'Agent specialized in fetching content from URLs.'
      ),
      sub_agents=[],
      instruction='Use the UrlContextTool to retrieve content from provided URLs.',
      tools=[
        url_context
      ],
    )
    plan_generator_agent_vertex_ai_search_agent = llm_agent.LlmAgent(
      name='Plan_Generator_Agent_vertex_ai_search_agent',
      model='gemini-1.5-flash',
      description=(
          'Agent specialized in performing Vertex AI Search.'
      ),
      sub_agents=[],
      instruction='Use the VertexAISearchTool to find information using Vertex AI Search.',
      tools=[
        VertexAiSearchTool(
          data_store_id='projects/583139806956/locations/global/collections/default_collection/dataStores/agrosignaldata_1777006287953'
        )
      ],
    )
    plan_generator_agent = llm_agent.LlmAgent(
      name='plan_generator_agent',
      model='gemini-1.5-flash',
      description=(
          'Generates complete selling plans for farmers'
      ),
      sub_agents=[],
      instruction='You are a selling plan generator for Malaysian farmers.\n\nWhen called with crop details:\n1. Search fama_market_data for price trends\n   Query: \"[crop] price [state] seasonal trend\"\n2. Use Google Search for current market conditions\n   Query: \"[crop] market Malaysia [current month]\"\n3. Combine both to generate:\n   - Best days to sell (Mon-Sun)\n   - Action steps for the farmer\n   - Timing recommendation\n   - Before vs After comparison\n\nFormat response as:\n📅 SELLING PLAN\nBest Days: [days]\nAction: [what to do]\nWhy Now: [reason based on data]\nExpected Price: RM [X]/kg',
      tools=[
        agent_tool.AgentTool(agent=plan_generator_agent_google_search_agent),
        agent_tool.AgentTool(agent=plan_generator_agent_url_context_agent),
        agent_tool.AgentTool(agent=plan_generator_agent_vertex_ai_search_agent)
      ],
    )
    recommendation_explainer_agent_google_search_agent = llm_agent.LlmAgent(
      name='Recommendation_Explainer_Agent_google_search_agent',
      model='gemini-1.5-flash',
      description=(
          'Agent specialized in performing Google searches.'
      ),
      sub_agents=[],
      instruction='Use the GoogleSearchTool to find information on the web.',
      tools=[
        GoogleSearchTool()
      ],
    )
    recommendation_explainer_agent_vertex_ai_search_agent = llm_agent.LlmAgent(
      name='Recommendation_Explainer_Agent_vertex_ai_search_agent',
      model='gemini-1.5-flash',
      description=(
          'Agent specialized in performing Vertex AI Search.'
      ),
      sub_agents=[],
      instruction='Use the VertexAISearchTool to find information using Vertex AI Search.',
      tools=[
        VertexAiSearchTool(
          data_store_id='projects/583139806956/locations/global/collections/default_collection/dataStores/agrosignaldata_1777006287953'
        )
      ],
    )
    recommendation_explainer_agent_url_context_agent = llm_agent.LlmAgent(
      name='Recommendation_Explainer_Agent_url_context_agent',
      model='gemini-1.5-flash',
      description=(
          'Agent specialized in fetching content from URLs.'
      ),
      sub_agents=[],
      instruction='Use the UrlContextTool to retrieve content from provided URLs.',
      tools=[
        url_context
      ],
    )
    recommendation_explainer_agent = llm_agent.LlmAgent(
      name='recommendation_explainer_agent',
      model='gemini-1.5-flash',
      description=(
          'Explains why a specific market was recommended'
      ),
      sub_agents=[],
      instruction='You are a market recommendation explainer for Malaysian farmers.\n\nWhen asked why a region was recommended:\n1. Search fama_market_data for:\n   Query: \"[crop] demand [recommended region]\"\n2. Search Google for:\n   Query: \"[crop] supply demand [region] Malaysia\"\n3. Explain in simple farmer-friendly language:\n   - Why this region has higher demand\n   - Why local price is lower\n   - Seasonal factors\n   - Any risks to consider\n\nFormat response as:\n🔍 WHY [REGION]?\nDemand: [explanation]\nPrice Advantage: RM [X] more per kg\nSeason: [seasonal context]\nRisk: [any warnings]',
      tools=[
        agent_tool.AgentTool(agent=recommendation_explainer_agent_google_search_agent),
        agent_tool.AgentTool(agent=recommendation_explainer_agent_vertex_ai_search_agent),
        agent_tool.AgentTool(agent=recommendation_explainer_agent_url_context_agent)
      ],
    )
    agro_signal_agent_google_search_agent = llm_agent.LlmAgent(
      name='AgroSignal_Agent_google_search_agent',
      model='gemini-1.5-flash',
      description=(
          'Agent specialized in performing Google searches.'
      ),
      sub_agents=[],
      instruction='Use the GoogleSearchTool to find information on the web.',
      tools=[
        GoogleSearchTool()
      ],
    )
    agro_signal_agent_url_context_agent = llm_agent.LlmAgent(
      name='AgroSignal_Agent_url_context_agent',
      model='gemini-1.5-flash',
      description=(
          'Agent specialized in fetching content from URLs.'
      ),
      sub_agents=[],
      instruction='Use the UrlContextTool to retrieve content from provided URLs.',
      tools=[
        url_context
      ],
    )
    agro_signal_agent_vertex_ai_search_agent = llm_agent.LlmAgent(
      name='AgroSignal_Agent_vertex_ai_search_agent',
      model='gemini-1.5-flash',
      description=(
          'Agent specialized in performing Vertex AI Search.'
      ),
      sub_agents=[],
      instruction='Use the VertexAISearchTool to find information using Vertex AI Search.',
      tools=[
        VertexAiSearchTool(
          data_store_id='projects/583139806956/locations/global/collections/default_collection/dataStores/agrosignaldata_1777006287953'
        )
      ],
    )
    root_agent = llm_agent.LlmAgent(
      name='AgroSignal_Agent',
      model='gemini-1.5-flash',
      description=(
          'Main agent that routes farmer requests'
      ),
      sub_agents=[market_analyzer_agent, plan_generator_agent, recommendation_explainer_agent],
      instruction='You are AgroSignal — the main AI agricultural advisor \nfor Malaysian farmers.\n\nYou have 3 specialist sub-agents. Route ALL requests:\n\nROUTING RULES:\n├── Farmer asks WHERE to sell\n│     → Call Market Analyzer Agent\n│     → Pass: crop, quantity, state, timing, transport\n│\n├── Farmer asks for a PLAN or STRATEGY  \n│     → Call Plan Generator Agent\n│     → Pass: crop, quantity, state, timing\n│\n├── Farmer asks WHY a market was recommended\n│     → Call Recommendation Explainer Agent\n│     → Pass: crop, state, recommended region\n│\n└── General farming questions\n      → Search fama_market_data directly\n      → Use Google Search for current news\n\nRULES:\n1. Never answer market questions directly\n2. Always delegate to the correct sub-agent\n3. Collect missing info before routing:\n   - crop type\n   - quantity (kg)\n   - state\n   - harvest timing\n   - transport method\n4. Respond in the same language as the farmer\n   (English or Bahasa Melayu)\n\nRESPONSE FORMAT:\nAlways end with:\n\"Want a full selling plan? Just ask!\"',
      tools=[
        agent_tool.AgentTool(agent=agro_signal_agent_google_search_agent),
        agent_tool.AgentTool(agent=agro_signal_agent_url_context_agent),
        agent_tool.AgentTool(agent=agro_signal_agent_vertex_ai_search_agent)
      ],
    )

    self.app = AdkApp(
        agent=root_agent,
        session_service_builder=self.session_service_builder
    )

  async def stream_query(self, query: str, user_id: str = 'test') -> Any:
    """Streaming query."""
    if self.app is None:
        raise RuntimeError("ADK app not initialized. Call set_up() first.")
    
    async for chunk in self.app.async_stream_query(
        message=query,
        user_id=user_id,
    ):
        yield chunk

app = AgentClass()
app.set_up()
