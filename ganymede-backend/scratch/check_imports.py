try:
    from notebooklm import ChatGoal, ChatResponseLength, ChatMode
    print("Imports successful from notebooklm root.")
    print("ChatGoal:", [e.name for e in ChatGoal])
    print("ChatResponseLength:", [e.name for e in ChatResponseLength])
except ImportError:
    try:
        from notebooklm.enums import ChatGoal, ChatResponseLength, ChatMode
        print("Imports successful from notebooklm.enums.")
    except ImportError as e:
        print(f"Import Error: {e}")
