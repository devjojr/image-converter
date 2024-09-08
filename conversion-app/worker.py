import os
import pika
from PIL import Image
import mysql.connector
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")

# email config
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

CONVERTED_FOLDER = "converted_images"

if not os.path.exists(CONVERTED_FOLDER):
    os.makedirs(CONVERTED_FOLDER)


# send email with an attachment
def send_email(to_email, subject, body, attachment_path=None):
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USERNAME
        msg["To"] = to_email
        msg["Subject"] = subject

        # adding body to email
        msg.attach(MIMEText(body, "plain"))

        # attach image if it exists
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={os.path.basename(attachment_path)}"
                )
                msg.attach(part)

        # send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Enable TLS
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            print(f"Email sent to {to_email} with attachment {attachment_path if attachment_path else 'without attachment'}.")
    except Exception as e:
        print(f"Error sending email: {e}")


def convert_image(image_path):
    try:
        with Image.open(image_path) as img:
            base_filename = os.path.splitext(os.path.basename(image_path))[0]
            new_filename = f"{base_filename}.png"
            new_filepath = os.path.join(CONVERTED_FOLDER, new_filename)
            img.save(new_filepath, "PNG")
            return new_filename, new_filepath
    except Exception as e:
        print(f"Error converting image: {e}")
        return None, None


# updating image status in db
def update_image_status(image_id, status, email=None, attachment_path=None):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE images SET status = %s WHERE id = %s",
        (status, image_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    # send email if conversion is successful
    if status == "Converted" and email:
        subject = "Your Image Has Been Converted!"
        body = "Hello,\n\nYour image has been successfully converted to PNG format. You can find the converted image attached to this email."
        send_email(email, subject, body, attachment_path)


# process messages from the queue
def callback(ch, method, properties, body):
    print(f"Received task: {body.decode()}")
    image_id = int(body.decode())

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, file_path, email FROM images WHERE id = %s", (image_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        filename, file_path, email = result

        # convert the image
        new_filename, new_filepath = convert_image(file_path)
        if new_filename and new_filepath:
            print(f"Image converted successfully: {new_filepath}")
            update_image_status(image_id, "Converted", email, new_filepath)
        else:
            update_image_status(image_id, "Failed")
    else:
        print(f"No image found with ID: {image_id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    ch.basic_ack(delivery_tag=method.delivery_tag)


# set up consumer of the queue
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue="image_conversion_queue", durable=True)

    print("Waiting for tasks. To exit, press CTRL+C")
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="image_conversion_queue", on_message_callback=callback)

    channel.start_consuming()
except Exception as e:
    print(f"Failed to connect to RabbitMQ: {e}")
