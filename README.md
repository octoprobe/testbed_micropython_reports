# Octoprobe report server

## About

This is base from https://github.com/aws-samples/python-fastapi-demo-docker.

## Prerequisites
- [Install Docker](https://docs.docker.com/get-docker/)
- [Install Docker Compose](https://docs.docker.com/compose/install/)

## Run locally as a developer

```bash
uv venv --python 3.13.3 .venv
source .venv/bin/activate
uv pip install -r server/requirements.txt
``` 

## Installation


1. 

```bash
cp .env.example .env
```

2. Run the Docker containers.
```
docker-compose up --build
```
At this point, the application should be running at [http://localhost:8000/](http://localhost:8000/). To stop the application, you can run:
```
docker-compose down
```
3. To restart or rebuild the application, you can run:
```
docker-compose up --build
```

## License

This project is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.

