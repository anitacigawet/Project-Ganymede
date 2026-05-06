import asyncio
from notebooklm import NotebookLMClient

async def main():
    try:
        client_instance = await NotebookLMClient.from_storage()
        async with client_instance as client:
            print("Client members:", dir(client))
            print("Notebooks members:", dir(client.notebooks))
            # Check if there is a way to get notebook details or update settings
            # client.notebooks.update? client.notebooks.get?
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
