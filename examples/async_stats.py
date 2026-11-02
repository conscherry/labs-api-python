import asyncio

from labs import AsyncLabsApiClient, LabsAPIError


async def main():
    try:
        async with AsyncLabsApiClient() as client:
            stats = await client.get_website_stats()
            bots = await client.list_bots(limit=3)
            print(stats)
            print(bots)
    except LabsAPIError as exc:
        print(f"Labs API error: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
