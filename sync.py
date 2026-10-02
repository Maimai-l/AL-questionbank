#!/usr/bin/env python3
"""Keep data/ in step with the `data` branch on GitHub.

    python3 sync.py update          更新代码(当前分支,只快进)并取回最新数据:日常只用这一条
    python3 sync.py pull            取回最新的数据库、题图、教材与页面到 data/
    python3 sync.py status          data/ 当前是哪个版本,有没有本地改动
    python3 sync.py push -m "说明"  把 data/ 的改动推上去(云端流水线用)

data/ 是 `data` 分支的 git worktree。这个分支始终只有一个提交:每次 push 都覆盖
上一版,所以仓库历史不会随数据库和图片的重新生成而增长。代价是 data/ 里不能保留
本地改动 —— pull 会拒绝覆盖未提交的改动,除非加 --force。详见 docs/data-sync.md。
"""
import argparse, os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
BRANCH = "data"
REMOTE = "origin"


def git(*args, cwd=ROOT, capture=False, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, text=True,
                       stdout=subprocess.PIPE if capture else None)
    if check and r.returncode != 0:
        sys.exit(f"失败: git {' '.join(args)}")
    return (r.stdout or "").strip() if capture else r.returncode


def is_worktree():
    return os.path.exists(os.path.join(DATA, ".git"))


def dirty():
    return git("status", "--porcelain", cwd=DATA, capture=True)


def pull(force=False, gc=False):
    git("fetch", REMOTE, f"+refs/heads/{BRANCH}:refs/remotes/{REMOTE}/{BRANCH}")
    if not is_worktree():
        if os.path.exists(DATA) and os.listdir(DATA):
            sys.exit(f"{DATA} 已存在且不是 worktree。先把它移走再 pull。")
        git("worktree", "prune")
        git("worktree", "add", "-B", BRANCH, DATA, f"{REMOTE}/{BRANCH}")
    else:
        if dirty() and not force:
            sys.exit("data/ 里有未提交的改动,pull 会覆盖它们。\n"
                     "确认不要这些改动就加 --force;要保留就先 push。")
        git("reset", "--hard", f"{REMOTE}/{BRANCH}", cwd=DATA)
        git("clean", "-fd", cwd=DATA)
    if gc:
        # 每次 push 都覆盖旧版本,旧对象只剩 reflog 引用;清掉它们释放磁盘
        git("reflog", "expire", "--expire=now", "--all")
        git("gc", "--prune=now", "--quiet")
    status()


def update(force=False):
    """The code (the checked-out branch, fast-forward only), then the data."""
    branch = git("rev-parse", "--abbrev-ref", "HEAD", capture=True)
    if git("status", "--porcelain", "--untracked-files=no", capture=True):
        sys.exit("代码目录有未提交的改动,先提交或撤销再 update。")
    git("fetch", REMOTE, branch)
    git("merge", "--ff-only", f"{REMOTE}/{branch}")
    print(f"代码: {branch} {git('log', '-1', '--format=%h %s', capture=True)}")
    pull(force=force)


def status():
    if not is_worktree():
        print("data/ 还没有取回。运行: python3 sync.py pull")
        return
    print(git("log", "-1", "--format=data 版本 %h  %ci%n说明: %s", cwd=DATA, capture=True))
    d = dirty()
    print(f"本地改动: {len(d.splitlines())} 个文件" if d else "本地改动: 无")


def push(message):
    if not is_worktree():
        sys.exit("data/ 不是 worktree,先 python3 sync.py pull")
    git("fetch", REMOTE, f"+refs/heads/{BRANCH}:refs/remotes/{REMOTE}/{BRANCH}")
    base = git("rev-parse", f"{REMOTE}/{BRANCH}", capture=True)
    head = git("rev-parse", "HEAD", cwd=DATA, capture=True)
    if base != head:
        sys.exit("远程 data 分支在你上次 pull 之后被别处更新过。\n"
                 "先把 data/ 的改动另存,pull 之后再合并,避免覆盖对方的结果。")
    git("add", "-A", cwd=DATA)
    if not dirty():
        print("data/ 没有改动,不需要 push")
        return
    # 单提交分支:改写唯一的提交,再用 lease 强推,确保覆盖的正是 pull 下来的那一版
    git("commit", "--amend", "-q", "-m", message, cwd=DATA)
    git("push", f"--force-with-lease={BRANCH}:{base}", REMOTE, f"HEAD:{BRANCH}", cwd=DATA)
    status()


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    up = sub.add_parser("update")
    up.add_argument("--force", action="store_true")
    pl = sub.add_parser("pull")
    pl.add_argument("--force", action="store_true", help="覆盖 data/ 里的本地改动")
    pl.add_argument("--gc", action="store_true", help="取回后清理旧版本占用的磁盘")
    sub.add_parser("status")
    ps = sub.add_parser("push")
    ps.add_argument("-m", "--message", required=True)
    a = p.parse_args()
    if a.cmd == "update":
        update(a.force)
    elif a.cmd == "pull":
        pull(a.force, a.gc)
    elif a.cmd == "status":
        status()
    else:
        push(a.message)


if __name__ == "__main__":
    main()
