import google.adk
import pkgutil

def find_adkapp(package, path):
    for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__, path + "."):
        try:
            mod = __import__(module_name, fromlist=['AdkApp'])
            if hasattr(mod, 'AdkApp'):
                print(f"Found AdkApp in {module_name}")
                return True
        except ImportError:
            pass
    return False

print("Searching for AdkApp in google.adk...")
if not find_adkapp(google.adk, "google.adk"):
    print("Not found in google.adk")

import vertexai
print("Searching for AdkApp in vertexai...")
if not find_adkapp(vertexai, "vertexai"):
    print("Not found in vertexai")
