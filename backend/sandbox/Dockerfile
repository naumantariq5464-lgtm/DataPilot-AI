FROM python:3.11-slim

# Increase pip timeout for slow connections + retry on failure
RUN pip install --no-cache-dir --timeout=300 --retries=5 \
    pandas==2.2.3 \
    numpy==2.1.3

# Create non-root user
RUN useradd --uid 1000 --no-create-home --shell /bin/false sandbox

# Create input data directory
RUN mkdir -p /data && chown sandbox:sandbox /data

# Copy the runner script
COPY runner.py /runner.py
RUN chown sandbox:sandbox /runner.py

# Switch to non-root user
USER sandbox

ENTRYPOINT ["python", "/runner.py"]
