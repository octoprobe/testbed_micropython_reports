import html
import io
import pathlib

from octoprobe.util_cached_git_repo import CachedGitRepo, GitSpec
from octoprobe.util_subprocess import SubprocessExitCodeException

from app.util_github import FormStartJob, ReturncodeStartJob

DIRECTORY_CACHE = pathlib.Path("/tmp/git_cache")


def fix_repos(form_startjob: FormStartJob) -> None:
    def fix_repo(repo: str | None) -> str:
        if repo is None:
            return ""
        if repo == "":
            return ""
        try:
            git_spec = GitSpec.parse_tolerant(git_ref=repo)
            return git_spec.render_git_spec
        except ValueError:
            return f"? {repo}"

    form_startjob.repo_firmware = fix_repo(form_startjob.repo_firmware)
    form_startjob.repo_tests = fix_repo(form_startjob.repo_tests)


def validate_repos(form_startjob: FormStartJob) -> ReturncodeStartJob:
    fix_repos(form_startjob=form_startjob)

    stdout = io.StringIO()
    repos: set[str] = set()
    for prefix, repo in (
        ("tests_", form_startjob.repo_tests),
        ("firmware_", form_startjob.repo_firmware),
    ):
        if repo is None:
            continue
        if repo == "":
            continue
        assert isinstance(repo, str)
        if repo in repos:
            continue
        repos.add(repo)
        CachedGitRepo.clean_directory_work_repo(directory_cache=DIRECTORY_CACHE)
        cache = CachedGitRepo(
            directory_cache=DIRECTORY_CACHE,
            git_spec=repo,
            prefix=prefix,
        )
        try:
            metadata = cache.clone(git_clean=False)
        except SubprocessExitCodeException as e:
            return ReturncodeStartJob(msg_error=f"Failed: {repo}", stdout=f"{e!r}")

        stdout.write(
            '<div style="border: 1px solid gray; background-color: #F0F0F0; padding: 10px; margin-bottom: 20px;">\n'
        )
        # stdout.write("<p>\n")
        stdout.write(
            f"""<h2><a href="{metadata.url_link}" target="_blank">{metadata.git_spec}</a></h2>\n"""
        )
        for command in (metadata.command_describe, metadata.command_log):
            stdout.write("<br/>\n")
            stdout.write(f"{html.escape(command.command)}\n")
            stdout.write("<br/>\n")
            _stdout = "<br/>".join(map(html.escape, command.stdout.splitlines()))
            stdout.write(
                f'<div style="padding-left: 20px;"><code>{_stdout}</code></div>\n'
            )
        # stdout.write("</p>\n")
        stdout.write("</div>\n")
    form_rc = ReturncodeStartJob(msg_ok="Ok", stdout=stdout.getvalue())
    return form_rc
