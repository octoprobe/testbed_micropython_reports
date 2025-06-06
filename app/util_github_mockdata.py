# gh api users/hmaerki
gh_users_hmaerki = {
    "login": "hmaerki",
    "id": 8708771,
    "node_id": "MDQ6VXNlcjg3MDg3NzE=",
    "avatar_url": "https://avatars.githubusercontent.com/u/8708771?v=4",
    "gravatar_id": "",
    "url": "https://api.github.com/users/hmaerki",
    "html_url": "https://github.com/hmaerki",
    "followers_url": "https://api.github.com/users/hmaerki/followers",
    "following_url": "https://api.github.com/users/hmaerki/following{/other_user}",
    "gists_url": "https://api.github.com/users/hmaerki/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/hmaerki/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/hmaerki/subscriptions",
    "organizations_url": "https://api.github.com/users/hmaerki/orgs",
    "repos_url": "https://api.github.com/users/hmaerki/repos",
    "events_url": "https://api.github.com/users/hmaerki/events{/privacy}",
    "received_events_url": "https://api.github.com/users/hmaerki/received_events",
    "type": "User",
    "user_view_type": "public",
    "site_admin": False,
    "name": "Hans Märki",
    "company": "Märki Informatik",
    "blog": "www.maerki.com",
    "location": "Switzerland",
    "email": "buhtig.hans.maerki@ergoinfo.ch",
    "hireable": None,
    "bio": None,
    "twitter_username": None,
    "public_repos": 82,
    "public_gists": 0,
    "followers": 6,
    "following": 2,
    "created_at": "2014-09-09T11:37:47Z",
    "updated_at": "2025-04-10T10:48:34Z",
}

# gh run list --repo=octoprobe/testbed_micropython --workflow=selfhosted_testrun --status in_progress --json name,number,status,conclusion,url,event,createdAt,startedAt
gh_progress = [
    {
        "conclusion": "",
        "createdAt": "2025-04-30T08:24:55Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 125,
        "startedAt": "2025-04-30T08:24:55Z",
        "status": "in_progress",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14750132324",
    }
]
# gh run list --repo=octoprobe/testbed_micropython --workflow=selfhosted_testrun --status queued --json name,number,status,conclusion,url,event,createdAt,startedAt
gh_queued = [
    {
        "conclusion": "",
        "createdAt": "2025-04-30T08:25:18Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 127,
        "startedAt": "2025-04-30T08:25:18Z",
        "status": "queued",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14750140112",
    },
    {
        "conclusion": "",
        "createdAt": "2025-04-30T08:25:08Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 126,
        "startedAt": "2025-04-30T08:25:08Z",
        "status": "queued",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14750136286",
    },
]

# gh run list --repo=octoprobe/testbed_micropython --workflow=selfhosted_testrun --status completed --json name,number,status,conclusion,url,event,createdAt,startedAt
gh_completed = [
    {
        "conclusion": "success",
        "createdAt": "2025-04-30T06:00:54Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 124,
        "startedAt": "2025-04-30T06:00:54Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14747775291",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-30T03:08:36Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 123,
        "startedAt": "2025-04-30T03:08:36Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14745842803",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-30T02:30:30Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 122,
        "startedAt": "2025-04-30T02:30:30Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14745422847",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-29T21:17:57Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 121,
        "startedAt": "2025-04-29T21:17:57Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14741519802",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-29T19:38:06Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 120,
        "startedAt": "2025-04-29T19:38:06Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14739857583",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-29T18:33:29Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 119,
        "startedAt": "2025-04-29T18:33:29Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14738725875",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-29T15:15:17Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 117,
        "startedAt": "2025-04-29T15:15:17Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14734877542",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-29T11:27:33Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 116,
        "startedAt": "2025-04-29T11:27:33Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14730108622",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-28T18:35:55Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 115,
        "startedAt": "2025-04-28T18:35:55Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14715229526",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-28T10:58:41Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 114,
        "startedAt": "2025-04-28T10:58:41Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14706101101",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-28T07:12:16Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 113,
        "startedAt": "2025-04-28T07:12:16Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14702360822",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-28T07:08:23Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 112,
        "startedAt": "2025-04-28T07:08:23Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14702304995",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-28T06:30:14Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 110,
        "startedAt": "2025-04-28T06:30:14Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14701733029",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-27T22:05:30Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 109,
        "startedAt": "2025-04-27T22:05:30Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14696563766",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-27T21:31:20Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 108,
        "startedAt": "2025-04-27T21:32:56Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14696322114",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-27T16:49:38Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 107,
        "startedAt": "2025-04-27T16:49:38Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14694163331",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-26T20:56:56Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 106,
        "startedAt": "2025-04-26T20:56:56Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14685026626",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-26T20:27:01Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 105,
        "startedAt": "2025-04-26T20:27:01Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14684821202",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-26T20:24:15Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 104,
        "startedAt": "2025-04-26T20:24:15Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14684800562",
    },
    {
        "conclusion": "success",
        "createdAt": "2025-04-26T20:21:35Z",
        "event": "workflow_dispatch",
        "name": "testbed_micropython",
        "number": 103,
        "startedAt": "2025-04-26T20:21:35Z",
        "status": "completed",
        "url": "https://github.com/octoprobe/testbed_micropython/actions/runs/14684778833",
    },
]
