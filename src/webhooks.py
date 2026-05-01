# Payment webhook handler
import hmac, hashlib

def verify_signature(payload: bytes, sig: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)

def handle_payment_event(event: dict):
    if event['type'] == 'payment.success':
        activate_subscription(event['user_id'])
