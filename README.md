# Resume Builder Web Application

This project is a web-based resume builder developed using Flask that allows users to create, manage, and export professional resumes. The application provides secure login using Google OAuth and stores user resume data in a SQLite database.

## Features

* User authentication using Google OAuth
* Create and manage resume details including skills, experience, and education
* Store user resume data securely using SQLite
* Export resume as a downloadable PDF
* Simple and user-friendly web interface

## Technologies Used

* Python
* Flask
* SQLite
* HTML & CSS
* Google OAuth
* xhtml2pdf for PDF generation

## Project Structure

```
resume-builder-flask-google-oauth
│
├── app.py
├── roles.json
│
├── templates
│   ├── index.html
│   ├── resume.html
│   ├── learn.html
│   └── export.html
│
├── static
│   └── css
│       └── style.css
│
├── README.md
├── LICENSE
└── .gitignore
```

## Installation

Clone the repository:

```
git clone https://github.com/yourusername/resume-builder-flask-google-oauth.git
```

Install required dependencies:

```
pip install -r requirements.txt
```

Create a `.env` file and add the following credentials:

```
FLASK_SECRET_KEY=your_secret_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

Run the application:

```
python app.py
```

Open the application in your browser to start creating resumes.

## Author

Sakthi Konda
Engineering Student
