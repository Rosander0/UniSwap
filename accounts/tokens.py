from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.contrib.auth import get_user_model

signer = TimestampSigner(salt="uniswap-email-verification")


def generate_verification_token(user):
    return signer.sign(str(user.pk))


def verify_token(token, max_age=86400 * 3):
    """Verify signed token and return the User instance or None."""
    user_model = get_user_model()
    try:
        user_id = signer.unsign(token, max_age=max_age)
        return user_model.objects.get(pk=user_id)
    except (BadSignature, SignatureExpired, user_model.DoesNotExist, ValueError):
        return None

