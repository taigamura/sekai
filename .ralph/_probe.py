import sys
mods = ["praw", "anthropic", "dependency_injector", "pytest", "click"]
for m in mods:
    try:
        __import__(m)
        print(m, "OK")
    except ImportError as e:
        print(m, "MISSING", e)
print(sys.version)
