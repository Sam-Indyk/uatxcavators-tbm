"""Git helpers for UATXSync (no Fusion imports, so they can be tested outside Fusion).

Only fast-forward updates are made: the clone is never reset, rebased or merged with a merge commit, and
nothing is pulled while another branch is checked out or the clone has local commits.
"""
import os
import shutil
import subprocess

_NO_WINDOW = 0x08000000 if os.name == "nt" else 0       # CREATE_NO_WINDOW: no console flash on Windows
_WIN_GIT = (r"C:\Program Files\Git\cmd\git.exe", r"C:\Program Files (x86)\Git\cmd\git.exe")


def find_git(configured=None):
    for g in (configured, shutil.which("git"), *(_WIN_GIT if os.name == "nt" else ())):
        if g and os.path.isfile(g):
            return g
    return None


def run(git, repo, *args, timeout=120):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    try:
        r = subprocess.run([git, "-C", repo, *args], capture_output=True, text=True, timeout=timeout, env=env,
                           creationflags=_NO_WINDOW, stdin=subprocess.DEVNULL)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return -1, "", f"git {' '.join(args)}: timed out after {timeout} s"
    except OSError as e:
        return -1, "", f"git {' '.join(args)}: {e}"


def head(git, repo):
    c, out, _ = run(git, repo, "rev-parse", "HEAD")
    return out if c == 0 else None


def info(git, repo):
    """Branch, HEAD, last commit line, short status (for the Status command and the log)."""
    d = {}
    for k, args in (("branch", ("rev-parse", "--abbrev-ref", "HEAD")), ("head", ("log", "-1", "--format=%h %cd %s", "--date=short")),
                    ("status", ("status", "--short", "--untracked-files=no"))):
        c, out, err = run(git, repo, *args, timeout=30)
        d[k] = out if c == 0 else "error: " + err
    return d


def update(git, repo, branch="main", remote="origin"):
    """Fetch and fast-forward. Returns {ok, msg, old, new, changed: [paths]}."""
    res = {"ok": False, "msg": "", "old": None, "new": None, "changed": []}
    c, cur, err = run(git, repo, "rev-parse", "--abbrev-ref", "HEAD", timeout=30)
    if c != 0:
        res["msg"] = "git: " + err
        return res
    if cur != branch:
        res["msg"] = f"clone is on branch '{cur}', not '{branch}': not pulled"
        return res
    c, _, err = run(git, repo, "fetch", "--quiet", remote, branch)
    if c != 0:
        res["msg"] = "fetch failed: " + err
        return res
    up = f"{remote}/{branch}"
    c1, behind, e1 = run(git, repo, "rev-list", "--count", f"HEAD..{up}", timeout=30)
    c2, ahead, e2 = run(git, repo, "rev-list", "--count", f"{up}..HEAD", timeout=30)
    if c1 or c2:
        res["msg"] = "rev-list failed: " + (e1 or e2)
        return res
    old = head(git, repo)
    res["old"] = res["new"] = old
    if int(behind) == 0:
        res.update(ok=True, msg="up to date" + (f" ({ahead} local commit(s) not pushed)" if int(ahead) else ""))
        return res
    if int(ahead) > 0:
        res["msg"] = f"clone and {up} have diverged ({ahead} local, {behind} remote commits): not pulled"
        return res
    c, out, err = run(git, repo, "merge", "--ff-only", "--quiet", up)
    if c != 0:
        res["msg"] = "fast-forward failed (local changes in files the update touches?): " + (err or out)
        return res
    new = head(git, repo)
    c, out, _ = run(git, repo, "diff", "--name-only", old, new, timeout=30)
    res.update(ok=True, new=new, changed=out.splitlines() if c == 0 else [], msg=f"pulled {behind} commit(s)")
    return res


def last_commit_of(git, repo, path):
    c, out, _ = run(git, repo, "log", "-1", "--format=%h %cd", "--date=short", "--", path, timeout=30)
    return out if c == 0 else ""


def commit_paths(git, repo, paths, message, push=False, branch="main", remote="origin"):
    c, _, err = run(git, repo, "add", "--", *paths, timeout=60)
    if c != 0:
        return False, "git add: " + err
    c, out, _ = run(git, repo, "diff", "--cached", "--quiet", timeout=30)
    if c == 0:
        return True, "nothing to commit"
    c, out, err = run(git, repo, "commit", "--quiet", "-m", message, "--", *paths, timeout=60)
    if c != 0:
        return False, "git commit: " + (err or out)
    if push:
        c, out, err = run(git, repo, "push", "--quiet", remote, branch)
        if c != 0:
            return False, "committed; push failed: " + (err or out)
        return True, "committed and pushed"
    return True, "committed"
