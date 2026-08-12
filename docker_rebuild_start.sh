# set -euox pipefail

git pull

docker compose down | true
docker compose rm --force | true
docker compose up --build -d
