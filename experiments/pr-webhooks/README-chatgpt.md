If you want to trigger a webhook when new commits are pushed to an existing Pull Request, the usual GitHub webhook event is:

* **`pull_request`** with action **`synchronize`**

This action is sent whenever commits are pushed to the PR's source branch after the PR has already been opened.

Example payload fields:

```json
{
  "action": "synchronize",
  "pull_request": {
    "number": 123
  }
}
```

Common `pull_request` actions include:

| Action        | When it happens                         |
| ------------- | --------------------------------------- |
| `opened`      | PR is created                           |
| `reopened`    | PR is reopened                          |
| `synchronize` | New commits are pushed to the PR branch |
| `closed`      | PR is closed (merged or not)            |

You can also subscribe to the **`push`** event, but that fires for *all* branch pushes and doesn't directly tell you whether the branch belongs to an open PR. For PR-specific automation, `pull_request` → `synchronize` is usually the right choice.

If you're using GitHub Actions instead of a webhook, the equivalent trigger is:

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
```

What are you building—an external webhook receiver, a GitHub App, or a GitHub Actions workflow?


# -------------------------------

For the repository [experiment_webhook_PR repository](https://github.com/hmaerki/experiment_webhook_PR?utm_source=chatgpt.com), you can only register a repository webhook if you have **admin access** to that repository. GitHub repository webhooks are configured in **Settings → Webhooks** of the repository. ([MPTooling][1])

### Option 1: Configure it in the GitHub UI

1. Open:
   `https://github.com/hmaerki/experiment_webhook_PR/settings/hooks`
2. Click **Add webhook**.
3. Set:

   * **Payload URL**: `https://your-server.example.com/github-webhook`
   * **Content type**: `application/json`
   * **Secret**: a random secret string
4. Choose **Let me select individual events**.
5. Select **Pull requests**.
6. Save the webhook. GitHub will send a `pull_request` event whenever a PR is opened, updated, closed, etc. A push to an existing PR generates the `pull_request` event with action `synchronize`. ([MPTooling][1])

### Option 2: Create it via the GitHub API

If you have a token with repository webhook write permissions, you can create it programmatically:

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/hmaerki/experiment_webhook_PR/hooks \
  -d '{
    "name": "web",
    "active": true,
    "events": ["pull_request"],
    "config": {
      "url": "https://your-server.example.com/github-webhook",
      "content_type": "json",
      "secret": "my-secret"
    }
  }'
```

GitHub's repository webhook API supports specifying the events (such as `pull_request`) and the target URL in the webhook configuration. ([GitHub Docs][2])

[1]: https://mptooling.github.io/pr-bot/register_github_webhook.html?utm_source=chatgpt.com "GH Webhook registration | pr-bot"
[2]: https://docs.github.com/en/enterprise-cloud%40latest/rest/repos/webhooks?utm_source=chatgpt.com "REST API endpoints for repository webhooks - GitHub Enterprise Cloud Docs"

# -------------------------------

Here's a minimal **FastAPI** example that receives GitHub `pull_request` webhooks and reacts to the `synchronize` action (new commits pushed to an existing PR).


### `main.py`

```python
from fastapi import FastAPI, Header, Request, HTTPException

app = FastAPI()


@app.post("/github-webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
):
    payload = await request.json()

    if x_github_event == "pull_request":
        action = payload.get("action")

        if action == "synchronize":
            pr_number = payload["pull_request"]["number"]
            repo = payload["repository"]["full_name"]

            print(
                f"PR #{pr_number} in {repo}: new commits pushed"
            )

            # Trigger your application logic here
            # e.g. queue a job, run tests, notify a service, ...

    return {"status": "ok"}
```

### Run locally

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Configure GitHub

In the repository:

1. Settings → Webhooks
2. Add webhook
3. Payload URL:

   ```
   https://your-domain.com/github-webhook
   ```
4. Content type:

   ```
   application/json
   ```
5. Select individual events:

   * Pull requests

### Verify the webhook signature (recommended)

Set a secret in GitHub and verify `X-Hub-Signature-256`:

```python
import hashlib
import hmac

from fastapi import FastAPI, Header, Request, HTTPException

app = FastAPI()

WEBHOOK_SECRET = b"replace-with-your-secret"


def verify_signature(body: bytes, signature: str) -> bool:
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET,
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@app.post("/github-webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None),
):
    body = await request.body()

    if not verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()

    if (
        x_github_event == "pull_request"
        and payload.get("action") == "synchronize"
    ):
        pr_number = payload["pull_request"]["number"]
        branch = payload["pull_request"]["head"]["ref"]

        print(
            f"PR #{pr_number} updated, branch={branch}"
        )

    return {"status": "ok"}
```

This is production-ready enough to:

* receive GitHub webhooks,
* authenticate them using the webhook secret,
* detect when a PR receives new commits (`action == "synchronize"`),
* trigger your own processing pipeline.
