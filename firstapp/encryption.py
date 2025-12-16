import boto3
import base64
from django.conf import settings

def encrypt_secret(plaintext):
    """Encrypt sensitive data using KMS"""
    kms = boto3.client(
        'kms',
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    
    response = kms.encrypt(
        KeyId=settings.KMS_KEY_ID,
        Plaintext=plaintext.encode()
    )
    
    return base64.b64encode(response['CiphertextBlob']).decode()

def decrypt_secret(ciphertext):
    """Decrypt sensitive data using KMS"""
    kms = boto3.client(
        'kms',
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    
    response = kms.decrypt(
        CiphertextBlob=base64.b64decode(ciphertext.encode())
    )
    
    return response['Plaintext'].decode()