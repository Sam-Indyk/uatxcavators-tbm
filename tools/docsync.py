"""Three-way check between a claude.ai project doc and its copy in docs/.

The claude.ai project "UATXcavators" holds docs at claude/<name>.md; this repo holds the same docs at docs/<name>.md.
docs/.sync.json records the content hash of each doc at the last sync, so a change on either side can be told apart
from a change on both sides.

  python tools/docsync.py compare <name> <file holding the project doc's current text>
      prints one of: in-sync | pull (project changed: copy it into docs/) | push (repo changed: write it to the project)
                     | conflict (both changed: do not overwrite either) | new-in-project | new-in-repo
  python tools/docsync.py mark <name>      record docs/<name>.md as synced (run after every pull or push)
  python tools/docsync.py list             list docs/*.md with their sync state against the record
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
STATE = DOCS / ".sync.json"


def digest(text):
    norm = "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip() + "\n"
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def load():
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def save(state):
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def repo_hash(name):
    f = DOCS / f"{name}.md"
    return digest(f.read_text(encoding="utf-8")) if f.exists() else None


def compare(name, project_file):
    p = Path(project_file)
    proj = digest(p.read_text(encoding="utf-8")) if p.exists() and p.stat().st_size else None
    repo = repo_hash(name)
    last = load().get(name)
    if proj and not repo:
        return "new-in-project"
    if repo and not proj:
        return "new-in-repo"
    if proj == repo:
        return "in-sync"
    if repo == last:
        return "pull"
    if proj == last:
        return "push"
    return "conflict"


def main(argv):
    if len(argv) >= 3 and argv[0] == "compare":
        print(compare(argv[1], argv[2]))
    elif len(argv) >= 2 and argv[0] == "mark":
        state = load()
        h = repo_hash(argv[1])
        if h is None:
            sys.exit(f"docs/{argv[1]}.md not found")
        state[argv[1]] = h
        save(state)
        print(f"{argv[1]} marked {h}")
    elif argv and argv[0] == "list":
        state = load()
        for f in sorted(DOCS.glob("*.md")):
            h = digest(f.read_text(encoding="utf-8"))
            print(f"{f.stem:28s} {h}  {'recorded' if state.get(f.stem) == h else 'changed since last sync'}")
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
