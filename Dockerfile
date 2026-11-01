FROM python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.lock ./
RUN pip install --no-cache-dir --require-hashes -r requirements.lock

COPY main.py ./

EXPOSE 8000

RUN useradd --create-home --uid 10001 appuser
USER appuser

CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
