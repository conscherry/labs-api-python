import os

from labs import LabsApiClient, LabsAPIError


def main():
    bot_id = os.getenv("DISCORD_BOT_ID")

    if not bot_id:
        raise RuntimeError("Set DISCORD_BOT_ID first.")

    try:
        with LabsApiClient() as client:
            result = client.post_stats(
                bot_id=bot_id,
                guild_count=30,
                user_count=4513,
                shard_count=1,
                uptime=3600,
                ping=45,
            )

            print("Stats response:", result)

    except LabsAPIError as exc:
        print(f"Stats submission failed: {exc}")

        if exc.status_code:
            print(f"HTTP status: {exc.status_code}")

        if exc.retry_after is not None:
            print(f"Retry after: {exc.retry_after} seconds")


if __name__ == "__main__":
    main()
