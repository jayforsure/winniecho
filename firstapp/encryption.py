import boto3
import base64
from django.conf import settings

def encrypt_secret(plaintext):
    """Encrypt sensitive data using AWS KMS (IAM Role based)"""
    kms = boto3.client(
        "kms",
        region_name="us-east-1"  # or your region
    )

    response = kms.encrypt(
        KeyId="YOUR_KMS_KEY_ID",
        Plaintext=plaintext.encode()
    )

    return base64.b64encode(response["CiphertextBlob"]).decode()


def decrypt_secret(ciphertext):
    """Decrypt sensitive data using AWS KMS (IAM Role based)"""
    kms = boto3.client("kms", region_name=settings.AWS_REGION)

    response = kms.decrypt(
        CiphertextBlob=base64.b64decode(ciphertext.encode())
    )

    return response["Plaintext"].decode()
