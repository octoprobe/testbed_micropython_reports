# set -euox pipefail

docker-compose down | true
docker-compose rm --force | true
docker-compose up --build -d
