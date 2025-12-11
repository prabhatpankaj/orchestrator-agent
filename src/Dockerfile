# ---------------------------------------------------------
# Base Python Image
# ---------------------------------------------------------
FROM python:3.12

# ---------------------------------------------------------
# Set working directory
# ---------------------------------------------------------
WORKDIR /app

# ---------------------------------------------------------
# Copy the entire project into container
# This ensures /app/src exists inside container
# ---------------------------------------------------------
COPY . /app

# ---------------------------------------------------------
# Ensure `src` is importable:
# Python must see /app as a package root
# ---------------------------------------------------------
ENV PYTHONPATH=/app

# ---------------------------------------------------------
# Install dependencies for orchestrator & UI
# ---------------------------------------------------------
RUN pip install --no-cache-dir -r src/requirements.txt

# ---------------------------------------------------------
# Default CMD is orchestrator execution.
# UI container overrides this with Streamlit command.
# ---------------------------------------------------------
CMD ["python", "-m", "src.executor.execute"]
