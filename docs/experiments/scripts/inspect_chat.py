import asyncio
from notebooklm import NotebookLMClient

async def main():
    try:
        client_instance = await NotebookLMClient.from_storage()
        async with client_instance as client:
            print("Chat members:", dir(client.chat))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
