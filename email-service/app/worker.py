import aio_pika
import asyncio
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings
from app.services.circuit_breaker import CircuitBreaker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EmailWorker:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self.connection = None
        self.channel = None
    
    async def connect(self):
        self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=settings.WORKER_PREFETCH_COUNT)
        self.queue = await self.channel.get_queue("email.queue")
        self.dlq = await self.channel.get_queue("failed.queue")
    
    async def send_email(self, to_email: str, subject: str, html_content: str):
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.FROM_EMAIL
        message["To"] = to_email
        message.attach(MIMEText(html_content, "html"))
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        
        logger.info(f"Email sent successfully to {to_email}")
    
    async def process_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                notification_id = body.get("notification_id")
                logger.info(f"Processing notification {notification_id}")
                
                if not self.circuit_breaker.can_proceed():
                    logger.warning("Circuit breaker OPEN, requeueing")
                    await message.reject(requeue=True)
                    await asyncio.sleep(5)
                    return
                
                # Simple template rendering
                variables = body.get("variables", {})
                html_content = f"<html><body><h1>Notification</h1><p>{json.dumps(variables)}</p></body></html>"
                
                await self.send_email(
                    to_email=body.get("user_email"),
                    subject=variables.get("subject", "Notification"),
                    html_content=html_content
                )
                
                self.circuit_breaker.record_success()
                logger.info(f"Successfully sent email for {notification_id}")
                
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                self.circuit_breaker.record_failure()
                
                retry_count = body.get("retry_count", 0)
                if retry_count >= settings.MAX_RETRIES:
                    logger.error(f"Max retries exceeded for {notification_id}, moving to DLQ")
                    await self.move_to_dlq(body)
                else:
                    body["retry_count"] = retry_count + 1
                    await asyncio.sleep(2 ** retry_count)
                    await message.reject(requeue=True)
    
    async def move_to_dlq(self, message_body: dict):
        message = aio_pika.Message(body=json.dumps(message_body).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
        await self.channel.default_exchange.publish(message, routing_key="failed.queue")
    
    async def start(self):
        await self.connect()
        logger.info("Email worker started, waiting for messages...")
        await self.queue.consume(self.process_message)
        await asyncio.Future()


async def main():
    worker = EmailWorker()
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")


if __name__ == "__main__":
    asyncio.run(main())

