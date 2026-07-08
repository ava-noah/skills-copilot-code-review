# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View active school announcements
- Authenticated teachers can create, edit, and delete announcements

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| POST   | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Remove a student from an activity                                   |
| POST   | `/auth/login?username=<username>&password=<password>`            | Login for teacher/admin users                                       |
| GET    | `/auth/check-session?username=<username>`                        | Validate saved teacher/admin session                                |
| GET    | `/announcements`                                                  | Get currently active announcements for public display               |
| GET    | `/announcements/manage?teacher_username=<username>`              | List all announcements for authenticated management                 |
| POST   | `/announcements?teacher_username=<username>`                     | Create a new announcement (message + expiration required)           |
| PUT    | `/announcements/{announcement_id}?teacher_username=<username>`   | Update an existing announcement                                     |
| DELETE | `/announcements/{announcement_id}?teacher_username=<username>`   | Delete an announcement                                              |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Data is stored in MongoDB. The application seeds example activities, teacher accounts, and a sample announcement when collections are empty.
