import argparse
import json
import time
from pathlib import Path
from typing import Any

import httpx


DEFAULT_API_URL = "http://127.0.0.1:8000/api/ingest"


def get_default_data_path() -> Path:
    """
    Expected project structure:
    agentic-crm-intelligence/
        backend/scripts/simulate_stream.py
        data/email-data-advanced.json
    """
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "data" / "email-data-advanced.json"


def load_emails(data_path: Path) -> list[dict[str, Any]]:
    if not data_path.exists():
        raise FileNotFoundError(f"Email data file not found: {data_path}")

    with data_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Email data must be a JSON array.")

    return data


def validate_email_payload(email: dict[str, Any], index: int) -> list[str]:
    required_fields = [
        "message_id",
        "sender",
        "subject",
        "body",
        "timestamp",
        "thread_id",
    ]

    errors = []

    for field in required_fields:
        if field not in email:
            errors.append(f"Email index {index}: missing field '{field}'")

    return errors


def post_email(
    client: httpx.Client,
    api_url: str,
    email: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    try:
        response = client.post(api_url, json=email, timeout=20.0)

        try:
            payload = response.json()
        except Exception:
            payload = {
                "raw_response": response.text,
            }

        if response.status_code in {200, 201}:
            return True, payload

        return False, {
            "status_code": response.status_code,
            "response": payload,
        }

    except httpx.ConnectError:
        return False, {
            "error": "CONNECTION_ERROR",
            "message": "Could not connect to FastAPI server. Is it running on port 8000?",
        }

    except httpx.TimeoutException:
        return False, {
            "error": "TIMEOUT",
            "message": "Request timed out while ingesting email.",
        }

    except Exception as exc:
        return False, {
            "error": "UNEXPECTED_ERROR",
            "message": str(exc),
        }


def simulate_stream(
    api_url: str,
    data_path: Path,
    speed: float,
    limit: int | None,
) -> None:
    emails = load_emails(data_path)

    if limit is not None:
        emails = emails[:limit]

    print("=" * 80)
    print("Agentic CRM Email Stream Simulator")
    print("=" * 80)
    print(f"API URL      : {api_url}")
    print(f"Data file    : {data_path}")
    print(f"Email count  : {len(emails)}")
    print(f"Speed        : {speed} email(s)/second")
    print("=" * 80)

    validation_errors = []

    for index, email in enumerate(emails, start=1):
        validation_errors.extend(validate_email_payload(email, index))

    if validation_errors:
        print("\nValidation errors found in source data:")
        for error in validation_errors:
            print(f"  - {error}")
        raise ValueError("Source data validation failed.")

    delay = 1.0 / speed if speed > 0 else 0

    success_count = 0
    duplicate_count = 0
    failure_count = 0

    with httpx.Client() as client:
        for index, email in enumerate(emails, start=1):
            message_id = email.get("message_id")
            sender = email.get("sender")
            subject = email.get("subject")

            print(f"\n[{index}/{len(emails)}] Ingesting {message_id}")
            print(f"Sender : {sender}")
            print(f"Subject: {subject}")

            ok, result = post_email(
                client=client,
                api_url=api_url,
                email=email,
            )

            if ok:
                success_count += 1
                data = result.get("data", {})
                print(
                    "Result : "
                    f"{data.get('status')} | "
                    f"{data.get('category')} | "
                    f"{data.get('urgency')} | "
                    f"Priority={data.get('priority_score')} | "
                    f"Human={data.get('requires_human')}"
                )
            else:
                error_response = result.get("response", {})
                error = error_response.get("error", {})

                if error.get("error_code") == "DUPLICATE_MESSAGE":
                    duplicate_count += 1
                    print("Result : Duplicate message ignored")
                else:
                    failure_count += 1
                    print("Result : Failed")
                    print(json.dumps(result, indent=2))

            if delay > 0 and index < len(emails):
                time.sleep(delay)

    print("\n" + "=" * 80)
    print("Simulation complete")
    print("=" * 80)
    print(f"Successful ingestions : {success_count}")
    print(f"Duplicates ignored    : {duplicate_count}")
    print(f"Failures              : {failure_count}")
    print("=" * 80)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay email-data-advanced.json into the FastAPI ingestion endpoint."
    )

    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"FastAPI ingestion URL. Default: {DEFAULT_API_URL}",
    )

    parser.add_argument(
        "--data-path",
        default=str(get_default_data_path()),
        help="Path to email-data-advanced.json.",
    )

    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Emails per second. Use 1 for dev, 10 for faster testing.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional number of emails to ingest from the start of the dataset.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    simulate_stream(
        api_url=args.api_url,
        data_path=Path(args.data_path),
        speed=args.speed,
        limit=args.limit,
    )