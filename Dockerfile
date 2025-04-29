FROM python:3.13.3-slim-bookworm

WORKDIR /server

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gh curl pgp unzip && \
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt-get update && \
    apt-get install -y gh && \
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
