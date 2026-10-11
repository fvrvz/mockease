#!/usr/bin/env bash
# ==============================================================================
# MockEase Local Development Orchestrator (Bash)
# ==============================================================================
# Starts or stops local development services:
# - PostgreSQL & Redis in Docker Compose
# - FastAPI Backend on host (port 8000)
# - Vue 3 / Vite Frontend on host (port 5173)
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

RUN_DIR="${ROOT_DIR}/.run"
LOG_DIR="${ROOT_DIR}/.logs"
BACKEND_PID_FILE="${RUN_DIR}/backend.pid"
FRONTEND_PID_FILE="${RUN_DIR}/frontend.pid"

mkdir -p "${RUN_DIR}" "${LOG_DIR}"

# ANSI Colors
BOLD="\033[1m"
GREEN="\033[32m"
BLUE="\033[34m"
YELLOW="\033[33m"
RED="\033[31m"
CYAN="\033[36m"
RESET="\033[0m"

log_info()  { echo -e "${BLUE}[INFO]${RESET} $*"; }
log_ok()    { echo -e "${GREEN}[OK]${RESET} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${RESET} $*"; }
log_err()   { echo -e "${RED}[ERROR]${RESET} $*"; }

banner() {
  echo -e "${BOLD}${CYAN}"
  echo "╔════════════════════════════════════════════════════════════╗"
  echo "║                  MockEase Dev Orchestrator                 ║"
  echo "║   DB: Docker (5432, 6379) | Backend: 8000 | UI: 5173       ║"
  echo "╚════════════════════════════════════════════════════════════╝"
  echo -e "${RESET}"
}

check_docker() {
  if ! command -v docker &>/dev/null; then
    log_err "Docker is not installed or not in PATH."
    exit 1
  fi
  if ! docker info &>/dev/null; then
    log_err "Docker daemon is not running. Please start Docker Desktop/daemon."
    exit 1
  fi
}

start_databases() {
  log_info "Starting PostgreSQL and Redis containers via Docker Compose..."
  cd "${ROOT_DIR}"
  docker compose up -d postgres redis

  log_info "Waiting for PostgreSQL to be healthy..."
  local retries=30
  while [ $retries -gt 0 ]; do
    if docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-mockease}" -d "${POSTGRES_DB:-mockease}" &>/dev/null; then
      break
    fi
    sleep 1
    retries=$((retries - 1))
  done

  if [ $retries -eq 0 ]; then
    log_err "PostgreSQL failed to report ready within 30 seconds."
    exit 1
  fi
  log_ok "PostgreSQL is ready on localhost:5432"

  log_info "Waiting for Redis to be healthy..."
  retries=20
  while [ $retries -gt 0 ]; do
    if [ "$(docker compose exec -T redis redis-cli ping 2>/dev/null | tr -d '\r')" = "PONG" ]; then
      break
    fi
    sleep 1
    retries=$((retries - 1))
  done
  log_ok "Redis is ready on localhost:6379"
}

setup_backend() {
  log_info "Configuring Backend environment..."
  cd "${ROOT_DIR}/backend"

  if [ ! -d ".venv" ]; then
    log_info "Creating virtualenv at backend/.venv..."
    python3 -m venv .venv
  fi

  # shellcheck disable=SC1091
  source .venv/bin/activate

  # Check if uvicorn installed
  if ! python -c "import uvicorn" &>/dev/null; then
    log_info "Installing backend dependencies..."
    pip install -r requirements.txt -r requirements-dev.txt
  fi

  log_info "Running database migrations (Alembic)..."
  alembic upgrade head
  log_ok "Backend environment verified and migrations up to date."
}

setup_frontend() {
  log_info "Configuring Frontend environment..."
  cd "${ROOT_DIR}/frontend"

  if [ ! -d "node_modules" ]; then
    log_info "Installing frontend dependencies (npm install)..."
    npm install
  fi
  log_ok "Frontend environment ready."
}

start_services() {
  local background=false
  if [ "$1" = "-d" ] || [ "$1" = "--background" ] || [ "$1" = "--detached" ]; then
    background=true
  fi

  check_docker
  start_databases
  setup_backend
  setup_frontend

  if [ "$background" = true ]; then
    log_info "Starting Backend in background (logging to .logs/backend.log)..."
    cd "${ROOT_DIR}/backend"
    source .venv/bin/activate
    nohup uvicorn src.main:app --reload --port 8000 > "${LOG_DIR}/backend.log" 2>&1 &
    echo $! > "${BACKEND_PID_FILE}"
    log_ok "Backend running [PID $(cat "${BACKEND_PID_FILE}")] -> http://localhost:8000"

    log_info "Starting Frontend in background (logging to .logs/frontend.log)..."
    cd "${ROOT_DIR}/frontend"
    nohup npm run dev > "${LOG_DIR}/frontend.log" 2>&1 &
    echo $! > "${FRONTEND_PID_FILE}"
    log_ok "Frontend running [PID $(cat "${FRONTEND_PID_FILE}")] -> http://localhost:5173"

    echo ""
    log_ok "All services started in background!"
    echo -e "  • Web UI:     ${BOLD}${GREEN}http://localhost:5173${RESET}"
    echo -e "  • API Docs:   ${BOLD}${CYAN}http://localhost:8000/api/docs${RESET}"
    echo -e "  • Stop with:  ${BOLD}./scripts/dev.sh stop${RESET}"
    echo ""
  else
    # Foreground mode with graceful shutdown trap
    log_info "Starting Backend & Frontend in foreground (Press Ctrl+C to stop both)..."

    cd "${ROOT_DIR}/backend"
    source .venv/bin/activate
    uvicorn src.main:app --reload --port 8000 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "${BACKEND_PID_FILE}"

    cd "${ROOT_DIR}/frontend"
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "${FRONTEND_PID_FILE}"

    cleanup() {
      echo ""
      log_info "Caught exit signal, shutting down services..."
      if kill -0 "${BACKEND_PID}" 2>/dev/null; then
        kill "${BACKEND_PID}" 2>/dev/null || true
      fi
      if kill -0 "${FRONTEND_PID}" 2>/dev/null; then
        kill "${FRONTEND_PID}" 2>/dev/null || true
      fi
      rm -f "${BACKEND_PID_FILE}" "${FRONTEND_PID_FILE}"
      log_ok "Host processes stopped."

      read -r -p "Stop Docker databases as well? [Y/n] " stop_db_answer
      stop_db_answer=${stop_db_answer:-Y}
      if [[ "$stop_db_answer" =~ ^[Yy]$ ]]; then
        cd "${ROOT_DIR}" && docker compose stop postgres redis
        log_ok "Docker databases stopped."
      else
        log_info "Docker databases kept running."
      fi
      exit 0
    }

    trap cleanup SIGINT SIGTERM EXIT

    echo ""
    log_ok "Services live:"
    echo -e "  • Web UI:   ${BOLD}${GREEN}http://localhost:5173${RESET}"
    echo -e "  • API Docs: ${BOLD}${CYAN}http://localhost:8000/api/docs${RESET}"
    echo ""

    wait "${BACKEND_PID}" "${FRONTEND_PID}" 2>/dev/null || true
  fi
}

stop_services() {
  log_info "Stopping development services..."

  # Stop Backend
  if [ -f "${BACKEND_PID_FILE}" ]; then
    PID=$(cat "${BACKEND_PID_FILE}")
    if kill -0 "${PID}" 2>/dev/null; then
      log_info "Stopping Backend [PID ${PID}]..."
      kill "${PID}" 2>/dev/null || true
    fi
    rm -f "${BACKEND_PID_FILE}"
  fi

  # Fallback check on port 8000
  if command -v lsof &>/dev/null; then
    PORT_8000_PID=$(lsof -ti:8000 2>/dev/null || true)
    if [ -n "${PORT_8000_PID}" ]; then
      log_info "Terminating residual process on port 8000 [PID ${PORT_8000_PID}]..."
      kill -9 "${PORT_8000_PID}" 2>/dev/null || true
    fi
  fi
  log_ok "Backend stopped."

  # Stop Frontend
  if [ -f "${FRONTEND_PID_FILE}" ]; then
    PID=$(cat "${FRONTEND_PID_FILE}")
    if kill -0 "${PID}" 2>/dev/null; then
      log_info "Stopping Frontend [PID ${PID}]..."
      kill "${PID}" 2>/dev/null || true
    fi
    rm -f "${FRONTEND_PID_FILE}"
  fi

  # Fallback check on port 5173
  if command -v lsof &>/dev/null; then
    PORT_5173_PID=$(lsof -ti:5173 2>/dev/null || true)
    if [ -n "${PORT_5173_PID}" ]; then
      log_info "Terminating residual process on port 5173 [PID ${PORT_5173_PID}]..."
      kill -9 "${PORT_5173_PID}" 2>/dev/null || true
    fi
  fi
  log_ok "Frontend stopped."

  # Stop Docker databases
  cd "${ROOT_DIR}"
  if command -v docker &>/dev/null && docker info &>/dev/null; then
    log_info "Stopping Docker PostgreSQL and Redis containers..."
    docker compose stop postgres redis || true
    log_ok "Docker database containers stopped."
  fi

  log_ok "All development services have been stopped."
}

status_services() {
  echo -e "${BOLD}MockEase Service Status:${RESET}"
  echo "----------------------------------------"

  # Docker containers
  if command -v docker &>/dev/null && docker info &>/dev/null; then
    cd "${ROOT_DIR}"
    docker compose ps postgres redis
  else
    echo "Docker is not running."
  fi

  echo "----------------------------------------"
  # Backend
  if [ -f "${BACKEND_PID_FILE}" ] && kill -0 "$(cat "${BACKEND_PID_FILE}")" 2>/dev/null; then
    echo -e "Backend:  ${GREEN}RUNNING${RESET} (PID $(cat "${BACKEND_PID_FILE}")) -> http://localhost:8000"
  elif command -v lsof &>/dev/null && lsof -ti:8000 &>/dev/null; then
    echo -e "Backend:  ${GREEN}RUNNING${RESET} (port 8000 active) -> http://localhost:8000"
  else
    echo -e "Backend:  ${RED}STOPPED${RESET}"
  fi

  # Frontend
  if [ -f "${FRONTEND_PID_FILE}" ] && kill -0 "$(cat "${FRONTEND_PID_FILE}")" 2>/dev/null; then
    echo -e "Frontend: ${GREEN}RUNNING${RESET} (PID $(cat "${FRONTEND_PID_FILE}")) -> http://localhost:5173"
  elif command -v lsof &>/dev/null && lsof -ti:5173 &>/dev/null; then
    echo -e "Frontend: ${GREEN}RUNNING${RESET} (port 5173 active) -> http://localhost:5173"
  else
    echo -e "Frontend: ${RED}STOPPED${RESET}"
  fi
  echo "----------------------------------------"
}

# Main command router
banner
ACTION="${1:-start}"
shift || true

case "${ACTION}" in
  start)
    start_services "$@"
    ;;
  stop)
    stop_services
    ;;
  restart)
    stop_services
    sleep 2
    start_services "$@"
    ;;
  status)
    status_services
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status} [-d|--background]"
    exit 1
    ;;
esac
