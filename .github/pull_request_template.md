## Description

<!-- Provide a brief description of the purpose of this PR and what problem it solves. -->

## Branch & Workflow Compliance

<!-- Ensure the source branch complies with the branch flow policy:
- PR targeting `dev`: source MUST be `feature/*`, `bugfix/*`, `docs/*`, or `refactor/*`.
- PR targeting `main`: source MUST be `dev` or `hotfix/*`.
-->

- [ ] Target branch is correct (`dev` for features/fixes/refactors, `main` for releases/hotfixes)
- [ ] Source branch naming adheres to convention (`feature/`, `bugfix/`, `docs/`, `refactor/`, `hotfix/`, or `dev`)

## Type of Change

- [ ] 🚀 New feature (`feature/`)
- [ ] 🐛 Bug fix (`bugfix/`)
- [ ] ♻️ Refactoring or optimization (`refactor/`)
- [ ] 📝 Documentation update (`docs/`)
- [ ] 🧪 Testing update (`test`)
- [ ] 🔧 CI/CD & tooling update (`ci`)
- [ ] 🧹 Maintenance / Chore (`chore`)

## Key Changes & Areas Affected

- [ ] **Backend** (`backend/`)
- [ ] **Frontend** (`frontend/`)
- [ ] **Docker / Infrastructure** (`Dockerfile`, `docker-compose.yml`, `.dockerignore`)
- [ ] **Workflows / CI** (`.github/workflows/`)

<!-- Summarize the key changes made in bullet points -->
- 

## Verification Checklist

### Code Quality & Standards
- [ ] Code builds without errors or warnings.
- [ ] Strict TypeScript followed: **Zero `any` types** in frontend code (`@typescript-eslint/no-explicit-any` passing).
- [ ] Frontend lint and type-check pass (`npm run lint`, `npm run type-check`).
- [ ] Frontend unit tests pass (`npm run test:unit`).
- [ ] Backend test suite passes (`pytest -v`).

### Containerization & Performance
- [ ] Docker images build cleanly (`docker compose build`).
- [ ] Test files, fixtures, caches, and dev dependencies are excluded from production Docker images.

### Security & Safety
- [ ] No secrets, API keys, or credentials committed.
- [ ] No unsafe dynamic evaluation in template engines or mock routes.
