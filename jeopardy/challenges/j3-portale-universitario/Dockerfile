ARG BASE_IMAGE=python@sha256:ed86c82274b3c69b52fb5820f358f0bd7df0b603332063cb5c6e32bd220c3e6e
FROM ${BASE_IMAGE} AS dependencies
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip check

FROM dependencies AS checked
COPY app/ /app/
COPY author/test_portal.py /checks/test_portal.py
RUN PYTHONPATH=/app python -m unittest discover -s /checks -v

FROM dependencies AS runtime
RUN groupadd --gid 10001 portal && useradd --uid 10001 --gid portal --no-create-home --shell /usr/sbin/nologin portal
COPY --from=checked /app/ /app/
COPY scenario.json /app/scenario.json
USER 10001:10001
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "2", "--timeout", "30", "--worker-tmp-dir", "/tmp", "--access-logfile", "-", "--error-logfile", "-", "portal:create_app()"]