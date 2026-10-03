"""What the tests share: the temporary folders the manager writes to, set before anything
from lib/ or manager/ is imported (so test files import this first), and the bank's
questions to make sets of."""
import atexit
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix="qb-test-")
os.environ["QB_WORK"] = os.path.join(TMP, "work")
os.environ["CAIE_EXPORTS"] = os.path.join(TMP, "exports")
sys.path.insert(0, ROOT)
atexit.register(shutil.rmtree, TMP, True)

from lib import paths  # noqa: E402

HAVE_DATA = os.path.exists(paths.DB)


def questions(exam="9709", component="3", n=6):
    """The first n questions of one paper of an exam."""
    from manager import bank
    return [r["id"] for r in bank.rows(exam) if str(r["component"]) == component][:n]
