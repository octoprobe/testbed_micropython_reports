set -euox

cd "$(dirname "$0")"

mkdir -p ./letsencrypt/etc ./letsencrypt/var
chown -R www-data:www-data ./letsencrypt

docker compose stop

docker run --rm --name certbot \
  --user "$(id -u www-data):$(id -g www-data)" \
  --group-add "$(id -g www-insecure)" \
  --network host \
  -v "./letsencrypt/etc:/etc/letsencrypt" \
  -v "./letsencrypt/var:/var/lib/letsencrypt" \
  certbot/certbot:v2.11.0 certonly --standalone \
  --cert-name reports.octoprobe.org \
  --http-01-address 92.205.27.173 \
  --http-01-port 80 \
  --config-dir /etc/letsencrypt \
  --work-dir /var/lib/letsencrypt \
  --logs-dir /var/lib/letsencrypt/log \
  -d reports.octoprobe.org \
  --email letsencrypt.hans.maerki@ergoinfo.ch \
  --agree-tos --no-eff-email \
  --non-interactive --keep-until-expiring

chown -R www-data:www-data ./letsencrypt

docker compose up -d

