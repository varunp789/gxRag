from worker.config import settings


def run_once() -> bool:
    """Consume one durable processing request and record its terminal state."""
    from app.services.asset_registry import run_queued_job
    from app.services.job_queue import dead_letter, dequeue
    from app.services.observability import emit

    job_id = dequeue(settings.poll_timeout_seconds)
    if job_id is None:
        return False
    result = run_queued_job(job_id)
    if result and result.status == "failed": dead_letter(job_id, "processing failed")
    emit("worker.job.finished", job_id=job_id, status=result.status if result else "missing")
    return True


def main() -> None:
    print(f"{settings.service_name} v{settings.service_version} listening on queue '{settings.queue_name}'")
    while True:
        run_once()


if __name__ == "__main__":
    main()
