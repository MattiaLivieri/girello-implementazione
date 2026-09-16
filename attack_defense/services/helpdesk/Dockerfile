# Stessa base Python fissata tramite digest usata da Document Vault.
FROM python@sha256:ed86c82274b3c69b52fb5820f358f0bd7df0b603332063cb5c6e32bd220c3e6e

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HELPDESK_DATA_DIR=/data

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip check

RUN groupadd --gid 10001 helpdesk \
    && useradd --uid 10001 --gid helpdesk --no-create-home helpdesk \
    && mkdir /data \
    && chown helpdesk:helpdesk /data

COPY app.py .
COPY static ./static

USER 10001:10001

EXPOSE 8082

CMD ["gunicorn", \
     "--bind", "0.0.0.0:8082", \
     "--workers", "1", \
     "--threads", "2", \
     "--timeout", "30", \
     "--worker-tmp-dir", "/tmp", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:create_app()"]
