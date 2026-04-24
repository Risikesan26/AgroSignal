import google.adk
import pkgutil

def list_submodules(package):
    print(f"Listing submodules of {package.__name__}:")
    for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        print(f"  {module_name}")

list_submodules(google.adk)

# Check some common locations
try:
    from google.adk.applications import AdkApp
    print("Found AdkApp in google.adk.applications")
except ImportError:
    try:
        from google.adk.apps import AdkApp
        print("Found AdkApp in google.adk.apps")
    except ImportError:
        try:
            from google.adk import AdkApp
            print("Found AdkApp in google.adk")
        except ImportError:
            print("AdkApp not found in google.adk common locations")
