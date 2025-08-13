# Octoprobe report server

## About

This is base from https://github.com/aws-samples/python-fastapi-demo-docker.

## Prerequisites
- [Install Docker](https://docs.docker.com/get-docker/)
- [Install Docker Compose](https://docs.docker.com/compose/install/)

## Run locally as a developer

```bash
uv venv --python 3.13.3
source .venv/bin/activate
uv pip install --upgrade -e .
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

## Run docker standalone on port 8000

```bash
docker build . --tag octoprobe-testbed_micropython-fastapi
docker run --rm -it -p 8000:80 -v $(pwd)/reports:/server/reports octoprobe-testbed_micropython-fastapi:latest
```

## Run docker standalone ipv6 (abandoned)

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


## GH_TOKEN

* github organization -> github settings page -> Third-party Access -> Personal access tokens -> Active tokens

Create token
* octoprobe_workflow
* Read access to organization events
* Read and Write access to organization self hosted runners
* Read access to metadata
* Read and Write access to actions, pull requests, and workflows

## Run docker and `gh`

```bash
source .env
docker run --rm -it \
-e GH_TOKEN=$GH_TOKEN \
octoprobe-testbed_micropython-fastapi:latest \
sh -c 'gh run list --repo=octoprobe/testbed_micropython --workflow=selfhosted_testrun --status completed --json name,number,status,url'
```

## Download testresults

```bash
ssh www-data@www.maerki.com tar zcf - -C /home/www/docker-octoprobe reports reports_metadata | tar xzf -
```
