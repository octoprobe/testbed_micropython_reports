import enum
import json
import os
import subprocess

from pydantic import BaseModel

from . import util_github_mockdata

MOCKED_GITHUB_RESULTS = False

# Provoke errors if the environment variable is NOT defined
EMAIL_USERS: list[str] = os.environ["EMAIL_USERS"].split(",")


class Default(enum.StrEnum):
    USER = "nobody"
    ARGUMENTS = "--flash-skip --only-test=RUN-TESTS_EXTMOD_HARDWARE_NATIVE"
    REPO_TESTS = "https://github.com/micropython/micropython.git@master"
    REPO_FIRMWARE = "https://github.com/micropython/micropython.git@master"


def subprocess_json(args: list[str]) -> dict | list:
    try:
        result = subprocess.run(args=args, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return data
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        raise


def gh_jobs() -> list[dict[str, str | int]]:
    if MOCKED_GITHUB_RESULTS:
        return [
            *util_github_mockdata.gh_queued,  # type: ignore[list-item]
            *util_github_mockdata.gh_progress,  # type: ignore[list-item]
            *util_github_mockdata.gh_completed,  # type: ignore[list-item]
        ]

    # Provoke errors if the environment variable is NOT defined
    _ = os.environ["GH_TOKEN"]

    list_result: list[dict[str, str | int]] = []
    for status in ("queued", "in_progress", "completed"):
        args = [
            "gh",
            "run",
            "list",
            "--repo=octoprobe/testbed_micropython_runner",
            "--workflow=testbed_micropython",
            "--status",
            status,
            "--json",
            "name,number,status,conclusion,url,event,createdAt,startedAt",
        ]

        data = subprocess_json(args=args)
        list_result.extend(data)
    return list_result


def gh_resolve_email(username: str) -> str | None:
    if username == "":
        return None

    def get_result() -> dict | list:
        if MOCKED_GITHUB_RESULTS:
            return util_github_mockdata.gh_users_hmaerki

        args = [
            "gh",
            "api",
            f"users/{username}",
        ]

        return subprocess_json(args=args)

    data = get_result()
    assert isinstance(data, dict)
    return data.get("email", None)


class FormStartJob(BaseModel):
    username: str
    arguments: str | None
    repo_tests: str | None
    repo_firmware: str | None


class ReturncodeStartJob(BaseModel):
    msg_ok: str | None = None
    msg_error: str | None = None


def gh_start_job(form_startjob: FormStartJob) -> ReturncodeStartJob:
    form_rc = ReturncodeStartJob()

    if form_startjob.username == Default.USER:
        form_rc.msg_error = "Skipped: User unknown..."
        return form_rc

    email_testreport: str | None = ""
    if form_startjob.username != "":
        email_testreport = gh_resolve_email(form_startjob.username)
        if email_testreport is None:
            form_rc.msg_error = (
                f"Could not resolve email address for '{form_startjob.username}'!"
            )
            return form_rc

    args = [
        "gh",
        "workflow",
        "run",
        "testbed_micropython.yml",
        "--repo=octoprobe/testbed_micropython_runner",
        "--field",
        f"arguments={form_startjob.arguments}",
        "--field",
        f"repo_firmware={form_startjob.repo_firmware}",
        "--field",
        f"repo_tests={form_startjob.repo_tests}",
        "--field",
        f"email_testreport='{email_testreport}'",
    ]

    try:
        _result = subprocess.run(
            args=args,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        form_rc.msg_error = f"Error executing command: {e}"
        return form_rc
    except json.JSONDecodeError as e:
        form_rc.msg_error = f"Error decoding JSON: {e}"
        return form_rc

    form_rc.msg_ok = "Job successfully added. The new job will be the topmost in below list. You might need to reload the page after a few seconds..."
    return form_rc
