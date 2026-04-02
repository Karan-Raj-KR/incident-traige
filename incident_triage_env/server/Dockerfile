FROM python:3.11-slim

WORKDIR /app

# Set PYTHONPATH for dual-import safe structure
ENV PYTHONPATH=/app

# Copy the entire incident_triage_env/ folder into /app/incident_triage_env/
COPY incident_triage_env/ /app/incident_triage_env/

# Copy scenarios/ folder into /app/incident_triage_env/scenarios/
COPY scenarios/ /app/incident_triage_env/scenarios/

# Install from server/requirements.txt
RUN pip install --no-cache-dir -r /app/incident_triage_env/server/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "incident_triage_env.server.app:app", "--host", "0.0.0.0", "--port", "8000"]
