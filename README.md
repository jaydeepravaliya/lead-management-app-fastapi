# Lead Management API

A FastAPI application for managing leads with SQLite storage.

## Running Locally
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd lead-management-app
   ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Run the application:
    ```bash
    python lead_management_app.py
    ```

4. Access the API at http://localhost:8000


## API Endpoints
1. POST /leads/: 
    Create a lead (public)
    Form data: first_name, last_name, email, resume (file)

2. GET /leads/: 
    List all leads (protected)
    Basic Auth: attorney/devpass

3. PATCH /leads/{lead_id}: 
    Update lead state to REACHED_OUT (protected)
    Basic Auth: attorney/devpass