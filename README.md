# EI-Requisition

## MVP Documentation

### Overview
The MVP of the EI-Requisition app provides a basic structure for managing requisitions with the following features:
1. User authentication and role-based access.
2. Requester Dashboard for creating and viewing requisitions.
3. Backend API for handling requisition data.
4. Static file support for serving CSS and JavaScript.

### Features
1. **Requester Dashboard**:
   - Create new requisitions with a title and description.
   - View a list of all requisitions with their statuses.

2. **Backend API**:
   - Endpoints for creating, retrieving, and managing requisitions.
   - Modular structure with routers for authentication, user management, and requisition handling.

3. **Static Files**:
   - Support for serving static assets like CSS and JavaScript.

### Project Structure
The project is organized into the following structure:
```
/Requisition_app
│
├── main.py                # Entry point for the FastAPI application
├── router/                # Contains modular routers for different functionalities
│   ├── auth.py            # Authentication-related routes
│   ├── user.py            # User management routes
│   ├── link.py            # Link-related routes
│   └── requests.py        # Requisition-related routes
│
├── templates/             # Directory for HTML templates
│   └── requester_dashboard.html
│
├── static/                # Directory for static assets like CSS and JS
│   ├── css/
│   └── js/
│
├── database/              # Contains database schema and setup scripts
│   ├── script.py          # Database initialization script
│   └── models.py          # Database models
│
├── services/              # Middleware and logging configuration
│   ├── middleware.py
│   └── logging_config.py
│
└── config.py              # Application configuration
```

### Flow Diagram
Below is a description of the flow diagram for the requisition process:

1. **Requester**:
   - Creates a requisition request via the Requester Dashboard.
   - The request is sent to the backend API and stored in the database.

2. **Storekeeper**:
   - Reviews the requisition and approves or denies it.
   - Updates the status in the database.

3. **Manager**:
   - Reviews the requisition after the storekeeper's approval.
   - Approves or denies the request and adds comments if necessary.

4. **CEO**:
   - Final review and decision on the requisition.
   - Updates the status to "Approved" or "Denied."

5. **Status Tracking**:
   - Each stage updates the requisition's status, which is visible on the dashboard.

### How to Run
1. Install dependencies:
   ```bash
   pip install fastapi uvicorn sqlalchemy jinja2
   ```

2. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

3. Access the application:
   - API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - Requester Dashboard: Open the corresponding HTML file in the `templates/` directory.

### Next Steps
- Implement dashboards for Storekeeper, Manager, and CEO.
- Add support for attachments and comments.
- Enhance the status tracking feature with a progress bar.

## 1. Project Overview & Structure
The project will have four main pages (or dashboards):

*# Requester Dashboard: Where the requester creates a new requisition request.
Storekeeper Dashboard: Where the storekeeper approves or denies the requisition.
Manager Dashboard: Where the manager reviews and approves/denies the request.
CEO Dashboard: The final step, where the CEO can approve/deny the request.
In addition, we'll need to:

Implement a status bar showing the request's approval stages.
Support attachments (like images) for each requisition.
Add comments at each stage for feedback.
2. Project Structure
We will organize the project with the following structure:


