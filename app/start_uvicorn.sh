set -euox
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
uvicorn app.main:app --host 0.0.0.0 --port 443 --ssl-keyfile=${SSL_KEY} --ssl-certfile=${SSL_CERT}
