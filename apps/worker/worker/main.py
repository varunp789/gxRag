from worker.config import settings


def main() -> None:
    print(
        f"{settings.service_name} v{settings.service_version} "
        f"listening on queue '{settings.queue_name}'"
    )


if __name__ == "__main__":
    main()

