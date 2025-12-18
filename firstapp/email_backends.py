from django.core.mail.backends.base import BaseEmailBackend
import boto3
from django.conf import settings

class SNSEmailBackend(BaseEmailBackend):
    """
    Email backend that sends emails via AWS SNS
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sns_client = boto3.client('sns', region_name=settings.AWS_SNS_REGION_NAME)
    
    def send_messages(self, email_messages):
        """
        Send email messages via SNS
        """
        if not email_messages:
            return 0
        
        sent_count = 0
        for message in email_messages:
            try:
                # Create message body
                body = f"""
Subject: {message.subject}
From: {message.from_email}
To: {', '.join(message.to)}

{message.body}
                """
                
                # Publish to SNS
                self.sns_client.publish(
                    TopicArn=settings.AWS_SNS_TOPIC_ARN,
                    Subject=message.subject[:100],  # SNS subject limit
                    Message=body
                )
                sent_count += 1
                
            except Exception as e:
                if not self.fail_silently:
                    raise
                print(f"SNS email error: {e}")
        
        return sent_count