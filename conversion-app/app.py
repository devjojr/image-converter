from flask import Flask, render_template, request, redirect, url_for, flash
import os
import mysql.connector
import pika
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# database config
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

# RabbitMQ config
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")

# upload folder for images
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/", methods=["POST"])
def upload():
    if "file" not in request.files or "email" not in request.form:
        flash("No image or email provided")
        return redirect(request.url)

    file = request.files["file"]
    email = request.form["email"]

    if file.filename == "" or email == "":
        flash("No image selected or email entered")
        return redirect(request.url)

    if file and allowed_file(file.filename):

        # secure file name
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        file.save(filepath)
        flash("File uploaded successfully!", "success")

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO images (filename, file_path, status, email) VALUES (%s, %s, %s, %s)",
            (filename, filepath, "Uploaded", email)
        )
        conn.commit()

        # getting last inserted ID to send to the queue
        image_id = cursor.lastrowid
        cursor.close()
        conn.close()

        # sending the image id to the queue
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
            channel = connection.channel()
            channel.queue_declare(queue="image_conversion_queue", durable=True)

            # publish image ID to the queue
            channel.basic_publish(
                exchange="",
                routing_key="image_conversion_queue",
                body=str(image_id),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                )
            )
            print(f"Task sent to the queue with ID: {image_id}")
            connection.close()
        except Exception as e:
            print(f"Error sending message to the queue: {e}")
            flash("Error processing image")

        return redirect(url_for("index"))
    else:
        flash("Invalid image type. Only JPG or JPEG images are allowed.", "error")
        return redirect(request.url)


# check for jpg or jpeg extension
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"jpg", "jpeg"}


if __name__ == "__main__":
    app.run(debug=True)
