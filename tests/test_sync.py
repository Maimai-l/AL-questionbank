"""sync.py against a throwaway upstream: a single-branch clone of main with the data
branch as a worktree, as on the user's machines.

    python3 -m unittest tests.test_sync
"""
import os, shutil, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIT = shutil.which("git")


def run(*args, cwd, env=None, check=True):
    r = subprocess.run(args, cwd=cwd, env=env, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if check and r.returncode:
        raise AssertionError(f"{' '.join(args)}: {r.stdout}")
    return r


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        up = self.up = os.path.join(self.tmp, "up")
        self.git("init", "-q", "-b", "main", up, cwd=self.tmp)
        shutil.copy(os.path.join(ROOT, "sync.py"), up)
        self.write(up, "manage.py", "")
        self.git("add", ".", cwd=up)
        self.git("commit", "-qm", "code", cwd=up)
        self.git("checkout", "-q", "--orphan", "data", cwd=up)
        self.git("rm", "-rqf", ".", cwd=up)
        self.write(up, "caie.db", "v1")
        self.git("add", ".", cwd=up)
        self.git("commit", "-qm", "data v1", cwd=up)
        self.git("checkout", "-q", "main", cwd=up)
        self.down = os.path.join(self.tmp, "down")
        self.git("clone", "-q", "--single-branch", "--branch", "main", up, self.down, cwd=self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def git(self, *args, cwd):
        return run(GIT, *args, cwd=cwd, env=self.env).stdout.strip()

    def write(self, d, name, text):
        with open(os.path.join(d, name), "w") as f:
            f.write(text)

    def sync(self, *args, env=None, check=True):
        return run(sys.executable, "sync.py", *args, "--no-auto" if args[0] == "pull" else "",
                   cwd=self.down, env=env or self.env, check=check)

    def new_data(self, text, files=("caie.db",)):
        """Replace the upstream data branch's single commit."""
        up = self.up
        self.git("checkout", "-q", "data", cwd=up)
        self.git("rm", "-rqf", ".", cwd=up)
        for f in files:
            self.write(up, f, text)
        self.git("add", ".", cwd=up)
        self.git("commit", "-q", "--amend", "-m", f"data {text}", cwd=up)
        self.git("checkout", "-q", "main", cwd=up)

    def data_file(self):
        with open(os.path.join(self.down, "data", "caie.db")) as f:
            return f.read()

    def test_pull_and_update(self):
        self.sync("pull")
        self.assertEqual(self.data_file(), "v1")
        self.new_data("v2")                       # rewritten, not a fast-forward
        self.sync("pull")
        self.assertEqual(self.data_file(), "v2")
        self.assertEqual(self.git("rev-list", "--count", "HEAD", cwd=os.path.join(self.down, "data")), "1")

    def test_concurrent_fetch_rewrites_fetch_head(self):
        """Another terminal's fetch rewrites .git/FETCH_HEAD with main between sync.py's
        fetch and its use of the result: data/ must still get the data commit."""
        self.sync("pull")
        self.new_data("v2")
        shim = os.path.join(self.tmp, "bin")
        os.mkdir(shim)
        main = self.git("rev-parse", "origin/main", cwd=self.down)
        with open(os.path.join(shim, "git"), "w") as f:
            f.write(f'#!/bin/sh\n"{GIT}" "$@"; rc=$?\n'
                    f'case "$1" in fetch) printf "{main}\\t\\tbranch \'main\' of up\\n" '
                    f'> "$(\"{GIT}\" rev-parse --git-common-dir)/FETCH_HEAD";; esac\nexit $rc\n')
        os.chmod(os.path.join(shim, "git"), 0o755)
        env = dict(self.env, PATH=shim + os.pathsep + self.env["PATH"])
        self.sync("pull", env=env)
        self.assertEqual(self.data_file(), "v2")
        self.assertTrue(self.git("cat-file", "-e", "origin/data:caie.db", cwd=self.down) == "")

    def test_pull_refuses_a_commit_without_the_database(self):
        self.sync("pull")
        self.new_data("code", files=("README.md",))
        r = self.sync("pull", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("不是数据提交", r.stdout)
        self.assertEqual(self.data_file(), "v1")   # data/ untouched

    def test_push_refuses_when_data_holds_code(self):
        self.sync("pull")
        d = os.path.join(self.down, "data")
        main = self.git("rev-parse", "origin/main", cwd=self.down)
        self.git("reset", "-q", "--hard", main, cwd=d)              # what the race left behind
        self.git("update-ref", "refs/remotes/origin/data", main, cwd=self.down)
        r = run(sys.executable, "sync.py", "push", "-m", "x", cwd=self.down, env=self.env, check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("不是数据提交", r.stdout)
        self.assertEqual(self.git("log", "-1", "--format=%s", "data", cwd=self.up), "data v1")
        self.sync("pull", "--force")                                # and pull repairs it
        self.assertEqual(self.data_file(), "v1")

    def test_push_replaces_the_single_commit(self):
        self.sync("pull")
        self.write(os.path.join(self.down, "data"), "caie.db", "v3")
        run(sys.executable, "sync.py", "push", "-m", "data v3", cwd=self.down, env=self.env)
        self.assertEqual(self.git("rev-list", "--count", "data", cwd=self.up), "1")
        self.assertEqual(self.git("show", "data:caie.db", cwd=self.up), "v3")


if __name__ == "__main__":
    unittest.main()
