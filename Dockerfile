# TubeFactory OCP - production image

FROM node:20-bookworm-slim AS web-builder

ARG NEXT_PUBLIC_API_BASE_URL=""
ARG NEXT_PUBLIC_API_PREFIX="/api/v1"

WORKDIR /app/apps/web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL} \
    NEXT_PUBLIC_API_PREFIX=${NEXT_PUBLIC_API_PREFIX}
RUN npm run build

FROM python:3.11-slim AS runtime

ARG NEXT_PUBLIC_API_BASE_URL=""
ARG NEXT_PUBLIC_API_PREFIX="/api/v1"

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_ENV=production \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    WEB_HOST=0.0.0.0 \
    WEB_PORT=3000 \
    NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL} \
    NEXT_PUBLIC_API_PREFIX=${NEXT_PUBLIC_API_PREFIX} \
    DATABASE_URL=sqlite+aiosqlite:////app/data/tubefactory.db

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nodejs \
    npm \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY apps ./apps
COPY packages ./packages
COPY --from=web-builder /app/apps/web/.next/standalone ./apps/web/
COPY --from=web-builder /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=web-builder /app/apps/web/public ./apps/web/public
COPY supervisord.conf /etc/supervisor/conf.d/tubefactory.conf

RUN mkdir -p /app/data /app/logs

EXPOSE 3000 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://127.0.0.1:${API_PORT}/health || exit 1

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/tubefactory.conf"]
