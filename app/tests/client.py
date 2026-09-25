import asyncio

from app.external.openlibrary.client import OpenLibraryClient


async def test():
    """Проверка работы клиента"""
    client = OpenLibraryClient()

    # Тест по ISBN
    data = await client.search_by_isbn("9780132350884")
    print(f"Found: {data}")

    # Тест по title+author
    data = await client.search_by_title_author("Clean Code", "Robert Martin")
    print(f"Found: {data}")

    await client.close()


asyncio.run(test())
