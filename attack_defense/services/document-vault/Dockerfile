# Mantiene la base Python originale, fissata tramite digest.
FROM python@sha256:ed86c82274b3c69b52fb5820f358f0bd7df0b603332063cb5c6e32bd220c3e6e

# Evita i file .pyc, invia subito i log e colloca i dati nel volume persistente.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VAULT_DATA_DIR=/data

WORKDIR /app

# Le dipendenze cambiano meno spesso del codice e restano in un layer separato.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip check

# Prepara un utente senza privilegi e la directory dati di sua proprieta'.
RUN groupadd --gid 10001 vault \
    && useradd --uid 10001 --gid vault --no-create-home vault \
    && mkdir /data \
    && chown vault:vault /data

COPY app.py .
COPY static/ ./static/

USER 10001:10001

EXPOSE 8081

# Conserva un worker con due thread e rende i log visibili da Docker Compose.
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8081", \
     "--workers", "1", \
     "--threads", "2", \
     "--timeout", "30", \
     "--worker-tmp-dir", "/tmp", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:create_app()"]
