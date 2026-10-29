from labs import LabsApiClient, LabsAPIError


def main():
    try:
        with LabsApiClient() as client:
            result = client.list_bots(
                limit=10,
                sort="-votes",
            )

            print(result)

    except LabsAPIError as exc:
        print(f"Labs API error: {exc}")
        if exc.status_code:
            print(f"HTTP status: {exc.status_code}")


if __name__ == "__main__":
    main()
