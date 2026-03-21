import hashlib
import hmac
import time

from fastapi import HTTPException, Request, status

from src.core.config import settings


async def validate_wavespeed_webhook_signature(request: Request) -> None:
    webhook_id = request.headers.get("webhook-id")
    webhook_timestamp = request.headers.get("webhook-timestamp")
    webhook_signature = request.headers.get("webhook-signature")

    if not webhook_id or not webhook_timestamp or not webhook_signature:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature headers",
        )

    raw_body = await request.body()
    if not _is_valid_wavespeed_signature(
        raw_body=raw_body,
        webhook_id=webhook_id,
        webhook_timestamp=webhook_timestamp,
        webhook_signature=webhook_signature,
        webhook_secret=settings.wavespeed.webhook_secret,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )


def _is_valid_wavespeed_signature(
    *,
    raw_body: bytes,
    webhook_id: str,
    webhook_timestamp: str,
    webhook_signature: str,
    webhook_secret: str,
    max_age_seconds: int = 300,
) -> bool:
    try:
        version, received_signature = webhook_signature.split(",", maxsplit=1)
    except ValueError:
        return False

    if version != "v3" or not received_signature:
        return False

    try:
        timestamp = int(webhook_timestamp)
    except ValueError:
        return False

    if abs(int(time.time()) - timestamp) > max_age_seconds:
        return False

    # WaveSpeed требует удалять только префикс "whsec_" без base64 decode.
    signing_key = webhook_secret.removeprefix("whsec_").encode("utf-8")
    signed_payload = f"{webhook_id}.{webhook_timestamp}.".encode("utf-8") + raw_body
    expected_signature = hmac.new(
        signing_key,
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, received_signature)
