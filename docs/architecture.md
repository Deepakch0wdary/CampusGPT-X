# CampusGPT X Architecture Documentation

This directory contains key architecture notes and guidelines for **CampusGPT X**.

## Services Architecture

- **`apps/backend`**: Built on FastAPI. Serves API endpoints, handles database connection pooling using SQLAlchemy, maps Pydantic models for validation, and manages exception boundaries.
- **`apps/frontend`**: SPA built on Vite, React, TypeScript, Tailwind CSS, and Material UI. Communicates with backend endpoints using standard JSON requests.
- **`prisma`**: Acts as the database schema orchestrator. Relational structures are defined in `schema.prisma`. Migrations are tracked and run via Prisma CLI.

## Key Design Patterns

1.  **Unified Responses**: All API endpoints return a standardized envelope structure:
    ```json
    {
      "success": true,
      "data": {}
    }
    ```
    Errors return:
    ```json
    {
      "success": false,
      "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable explanation.",
        "details": {}
      }
    }
    ```
2.  **Explicit Dependency Injection**: FastAPI dependencies (like database sessions `get_db`) are injected using standard `Depends()` signatures, promoting unit testability.
3.  **Tailwind & MUI Style Synergy**: Tailwind handles macro layout variables, alignment flexboxes, and padding utilities, while MUI is utilized for high-density elements like data grid panels. Theme configurations share structural design tokens.
