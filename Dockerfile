ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

FROM base AS builder
COPY requirements.txt ./
RUN python3 -m pip install --upgrade pip \
    && python3 -m pip wheel --wheel-dir /wheels -r requirements.txt

FROM base AS development
COPY requirements.txt ./
RUN python3 -m pip install --upgrade pip \
    && python3 -m pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python3", "-m", "src.main"]

FROM base AS production
COPY requirements.txt ./
COPY --from=builder /wheels /wheels
RUN python3 -m pip install --upgrade pip \
    && python3 -m pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

RUN addgroup --system app && adduser --system --ingroup app app
COPY src ./src
COPY data ./data
COPY migrations ./migrations
COPY scripts ./scripts
COPY load_sample_data.py ./load_sample_data.py
RUN mkdir -p /app/data /app/backups && chown -R app:app /app

USER app
EXPOSE 8000
CMD ["python3", "-m", "src.main"]
