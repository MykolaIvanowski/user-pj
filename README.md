 **User Service — FastAPI Microservice**

A lightweight, fully asynchronous, production‑ready microservice for managing users. Built with FastAPI, SQLAlchemy 2.0 async, Pydantic v2, and event‑driven patterns (Kafka).

This service provides clean architecture, strong separation of concerns, structured logging, and a complete test suite.


**Features**

* Full **CRUD** for user entities
* **Async** stack (FastAPI + SQLAlchemy async)
* **Soft & hard delete**
* **Pydantic v2** schemas with aliasing
* **Structured logging** via structlog
* **Kafka events** (`user.created`, `user.updated`, `user.deleted.*`)
* **Integration tests** using httpx + ASGITransport
* Clean architecture: controller → service → repository → model
