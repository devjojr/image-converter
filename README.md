# Image Converter

This project is a web-based application that allows users to upload JPEG/JPG images and converts them to PNG format. The application is built using Flask for the web framework, RabbitMQ for message queuing, and MySQL for database management. The application also includes email notifications to inform users when their images have been successfully converted and attaches the converted image.

## Features

- **Image Upload**
- **Image Conversion**
- **Asynchronous Processing**
- **Email Notifications**

## Setup Instructions

### Prerequisites

- **Python**
- **MySQL Server**
- **RabbitMQ Server**

### Installation

1. Clone the Repository

   ```bash
   git clone https://github.com/devjojr/image-converter.git
   cd image-converter
   ```

2. Set up the virtual environment

   ```bash
   python -m venv venv

   source venv/bin/activate
   ```

3. Install the Dependencies

   ```bash
   cd conversion-app

   pip install -r requirements.txt
   ```

4. Configure the environment variables

   ```txt
   SECRET_KEY=your_secret_key
   DB_HOST=localhost
   DB_USER=your_user_name
   DB_PASSWORD=your_db_password
   DB_NAME=image_conversion
   RABBITMQ_HOST=localhost
   SMTP_SERVER=your_smtp_server
   SMTP_PORT=587
   SMTP_USERNAME=your_email@example.com
   SMTP_PASSWORD=your_email_password
   ```

5. Set up MySQL database

   ```sql
   CREATE DATABASE image_conversion;
   USE image_conversion;

   CREATE TABLE images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

6. Run Flask App

   ```bash
   python app.py
   ```

7. Start Worker Process

   ```bash
   python worker.py
   ```

## Usage

- Upload a JPEG/JPG image and provide your email.
- The app will convert the image to PNG and send an email notification with the converted image attached.
