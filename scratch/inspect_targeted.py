import google.adk.agents.llm_agent as llm_agent
import vertexai.preview.reasoning_engines as reasoning_engines

print("Reasoning Engines dir:", dir(reasoning_engines))

try:
    from google.adk.applications import adk_app
    print("Found google.adk.applications.adk_app")
    print("Dir:", dir(adk_app))
except ImportError:
    print("google.adk.applications.adk_app not found")

try:
    from google.adk.apps import adk_app
    print("Found google.adk.apps.adk_app")
except ImportError:
    print("google.adk.apps.adk_app not found")

try:
    # Some versions might have it in the reasoning_engines but under a different name or path
    import vertexai.preview.reasoning_engines.templates as templates
    print("Templates dir:", dir(templates))
except ImportError:
    print("Templates not found")
