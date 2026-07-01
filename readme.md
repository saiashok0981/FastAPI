# FastAPI Trials

This repository serves as a documentation and experimental workspace for exploring **FastAPI** features and implementations.

## Project Overview

The project is structured to test various functionalities within a FastAPI framework, including database interactions, authentication, and service-based architecture.

### Key Components

* **Routers**: Modularized API endpoints handling specific domain logic:
* `auth.py`: Authentication processes.


* `urls.py`: URL management.


* `analytics.py`: Analytics tracking.


* `health.py`: System health checks.




* **Services**: Business logic layer isolating functional tasks:
* `shortner.py`: URL shortening logic.


* `qr.py`: QR code generation.


* `analytics.py`: Analytics processing.




* **Database & Models**: Database configuration and ORM models for data persistence.


* **CRUD**: Database interaction operations.


* **Testing**: Includes unit tests and coverage reports to ensure reliability.



### Setup

* **Environment**: Dependencies are managed via `requirements.txt`.


* **Infrastructure**: Includes configuration for database setup, specifically `postgres-setup.yaml`.