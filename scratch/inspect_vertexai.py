import vertexai
import pkgutil

def list_submodules(package):
    print(f"Listing submodules of {package.__name__}:")
    for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        print(f"  {module_name}")

try:
    import vertexai.preview.reasoning_engines as re
    print("Found vertexai.preview.reasoning_engines")
    print(f"Dir: {dir(re)}")
except ImportError as e:
    print(f"Could not import vertexai.preview.reasoning_engines: {e}")

try:
    import vertexai.agent_engines as ae
    print("Found vertexai.agent_engines")
    print(f"Dir: {dir(ae)}")
except ImportError as e:
    print(f"Could not import vertexai.agent_engines: {e}")
