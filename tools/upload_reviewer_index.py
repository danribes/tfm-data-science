"""Put the reviewer index on the Space, and take it off again.

    PYTHONPATH=. python tools/build_reviewer_index.py --out /tmp/reviewer.db
    PYTHONPATH=. python tools/upload_reviewer_index.py --file /tmp/reviewer.db
    PYTHONPATH=. python tools/upload_reviewer_index.py --remove   # when done

This runs from a machine holding the private corpus, because CI does not have
it and never will: the books are not in the repository. The deploy workflow
keeps `data/rag/reviewer.db` out of its delete patterns for the same reason.

What this publishes is third-party copyrighted text on a third-party host,
and the current deployment serves it openly by explicit decision of the
author. `--remove` is half the point of this file: it is the way to stop
serving it.

Needs HF_TOKEN in the environment or a prior `huggingface-cli login`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = "danribes/evo-espana-api"
REMOTE = "data/rag/reviewer.db"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", type=Path, help="local reviewer index to upload")
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--remove", action="store_true",
                    help="delete the index from the Space and stop serving the books")
    args = ap.parse_args()

    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("pip install huggingface_hub")
        return 1
    api = HfApi()

    if args.remove:
        api.delete_file(path_in_repo=REMOTE, repo_id=args.repo, repo_type="space",
                        commit_message="retirar el índice de revisión")
        print(f"removed {REMOTE} from {args.repo}")
        print("Also clear EVO_RAG_DB and EVO_RAG_MODE in the Space settings,")
        print("or the service will look for a file that is no longer there.")
        return 0

    if not args.file or not args.file.is_file():
        print("--file is required unless --remove")
        return 1
    size = args.file.stat().st_size / 1e6
    print(f"uploading {args.file.name} ({size:.0f} MB) to {args.repo}:{REMOTE}")
    api.upload_file(path_or_fileobj=str(args.file), path_in_repo=REMOTE,
                    repo_id=args.repo, repo_type="space",
                    commit_message="índice de revisión")
    print("done. In the Space settings, set:")
    print(f"  EVO_RAG_DB    = /app/{REMOTE}")
    print()
    print("RESTRICTED_COLLECTIONS is empty, so this corpus — copyrighted manuals")
    print("included — is served to anyone, with no credential. Putting the names")
    print("back in rag/config.py and setting EVO_RAG_TOKEN closes it again.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
