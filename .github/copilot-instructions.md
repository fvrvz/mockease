# GitHub Copilot Instructions for MockEase

## Project Overview
MockEase is a mock API management platform built with:
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2 (asyncpg), PostgreSQL 16, Redis 7, Pydantic v2.
- **Frontend**: Vue 3 (Composition API `<script setup lang="ts">`), TypeScript, Pinia, Vue Router 5, Vite, modern dark slate CSS design system.
- **Infrastructure**: Multi-stage Dockerfiles and Docker Compose.

## Pull Request Review Instructions
When reviewing Pull Requests for this repository:
1. **Branch Flow & Architecture**:
   - Ensure PRs targeting `main` come strictly from `dev` or `hotfix/*`.
   - Ensure PRs targeting `dev` come from `feature/*`, `bugfix/*`, `docs/*`, or `refactor/*`.
   - Ensure relationships between User -> Applications -> Controllers -> Endpoints maintain cascade rules and proper asyncpg greenlet handling (use `selectinload` when returning models with relations).
2. **Mock Runtime Engine**:
   - Verify that routes under `/mock/{app_slug}/{path:path}` correctly validate authentication hierarchy (`Endpoint` -> `Controller` -> `Application`).
   - Check that dynamic template macros (`{{uuid}}`, `{{timestamp}}`, `{{random.*}}`, `{{request.*}}`) are safely evaluated without remote code execution risks.
   - Verify that status codes, artificial latency delays, and headers are preserved.
3. **Frontend Standards**:
   - Verify Vue 3 components use `<script setup lang="ts">` with strongly typed props and emits.
   - Avoid generic `window.alert()` or `window.confirm()`; use the reusable `ConfirmDialog` component.
   - Ensure input fields prevent unwanted browser spellcheck/autocomplete interception when handling code or JSON.
4. **Testing & Code Quality**:
   - If backend endpoints or models were modified, verify that unit tests in `backend/tests` cover the changes.
   - If frontend components were modified, ensure `npm run type-check` and `npm run test:unit` pass.
