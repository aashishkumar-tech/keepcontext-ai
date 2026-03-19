        FROM python:3.12-slim AS base

        WORKDIR /app

        # Install uv
RUN pip install --no-cache-dir uv

# Install dependencies
COPY requirements.txt pyproject.toml ./
RUN uv pip install --system --no-cache -r requirements.txt

        # Copy source code
        COPY src/ src/

# Install project (editable not needed in container)
RUN uv pip install --system --no-cache .

        # Create non-root user
        RUN useradd --create-home appuser
        USER appuser

        EXPOSE 8000

CMD ["uvicorn", "keepcontext_ai.main:get_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
