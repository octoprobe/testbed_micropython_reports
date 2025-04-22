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
At this point, the application should be running at [http://localhost:443](http://localhost:443). To stop the application, you can run:
```
docker-compose down
```
3. To restart or rebuild the application, you can run:
```
docker-compose up --build
```

## Run docker standalone (abandoned)

docker run --rm -it -p 80:80 octoprobe-testbed_micropython-fastapi:latest

## Run docker standalone (abandoned)

```bash
docker run --rm -it --ip 0.0.0.0 -p 8000:8000 octoprobe-testbed_micropython-fastapi:latest

docker run --rm -it --ip6 2a00:1169:110:49c0:: -p 8000:8000 octoprobe-testbed_micropython-fastapi:latest
sudo netstat -tulpn | grep 8000
tcp        0      0 0.0.0.0:8000            0.0.0.0:*               LISTEN      97505/docker-proxy
tcp6       0      0 :::8000                 :::*                    LISTEN      97512/docker-proxy
==> ok  
curl -6 "http://[2a00:1169:110:49c0::]:8000/static/static.txt"
==> Ok
http://reports.octoprobe.org:8000/static/static.txt
==> timeout

docker run --rm -it --ip6 2a00:1169:110:49c0:: -p 80:8000 octoprobe-testbed_micropython-fastapi:latest
==> listen tcp4 0.0.0.0:80: bind: address already in use.
```
==> could not make v6 docker container visible to the world...

## License

This project is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.

