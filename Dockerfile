FROM python:3.13.3-slim-bookworm

WORKDIR /server

# Install system dependencies
RUN apt-get update && apt-get install -y git && \
    apt-get purge -y curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy project
COPY ./pyproject.toml /server/
COPY ./README.md /server/
COPY ./app /server/app

# Install Python dependencies
RUN pip install --no-cache-dir .

# Hack
RUN mkdir -p /var/www
RUN chmod a+rwx /var/www

# Expose the port the app runs in
EXPOSE 80

# Define the command to start the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
