from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings
from app.models.order import Order


def create_order_confirmation_html(order: Order) -> str:
    """Generate HTML email template for order confirmation."""
    items_html = ""
    for item in order.items:
        items_html += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">{item.product.name}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{item.quantity}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">${item.price_at_purchase:.2f}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">${(item.quantity * item.price_at_purchase):.2f}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background-color: #f9f9f9; }}
            .order-details {{ background-color: white; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th {{ background-color: #f0f0f0; padding: 10px; text-align: left; }}
            .total {{ font-size: 18px; font-weight: bold; text-align: right; margin-top: 20px; padding: 15px; background-color: #e8f5e9; }}
            .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Order Confirmation</h1>
            </div>
            <div class="content">
                <p>Hi {order.user.email},</p>
                <p>Thank you for your order! We've received your payment and are processing your order.</p>
                
                <div class="order-details">
                    <h2>Order Details</h2>
                    <p><strong>Order ID:</strong> #{order.id}</p>
                    <p><strong>Status:</strong> {order.status.upper()}</p>
                    
                    <h3>Items Purchased</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th style="text-align: center;">Quantity</th>
                                <th style="text-align: right;">Price</th>
                                <th style="text-align: right;">Subtotal</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                    
                    <div class="total">
                        Total: ${order.total_amount:.2f}
                    </div>
                </div>
                
                <p>We'll send you another email when your order ships.</p>
                <p>If you have any questions, please don't hesitate to contact us.</p>
            </div>
            <div class="footer">
                <p>© 2026 E-Commerce API. All rights reserved.</p>
                <p>This is an automated email. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """


async def send_order_confirmation_email(to_email: str, order: Order) -> None:
    """Send order confirmation email via SMTP."""
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        print(
            f"⚠️  Email not configured - would send to {to_email} for order #{order.id}"
        )
        return

    message = MIMEMultipart("alternative")
    message["From"] = settings.FROM_EMAIL
    message["To"] = to_email
    message["Subject"] = f"Order Confirmation - Order #{order.id}"

    html_content = create_order_confirmation_html(order)
    message.attach(MIMEText(html_content, "html"))

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        print(f"✅ Order confirmation email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {str(e)}")
        # Don't raise - email failure shouldn't break the order flow
