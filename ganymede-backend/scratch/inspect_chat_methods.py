import asyncio
from notebooklm import NotebookLMClient

async def main():
    try:
        client_instance = await NotebookLMClient.from_storage()
        async with client_instance as client:
            print("Chat configure help:", help(client.chat.configure))
            print("Chat set_mode help:", help(client.chat.set_mode))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
