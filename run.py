
import subprocess
import shutil
import sys
import os
from argparse import ArgumentParser

class LintInfo:
    def __init__(self, lang: str, desc: str, example: str, use_instead: str):
        self.lang = lang
        self.desc = desc
        self.example = example
        self.use_instead = use_instead

def err(*msg: str, code = 1):
    print("\x1b[31;1merror\x1b[0m: {}".format(" ".join(msg)), file=sys.stderr)
    exit(code)


def ensure_cmd(cmd: str):
    if shutil.which(cmd) is None:
        err(f"missing command '{cmd}', make sure it has been installed and added to PATH")


def clone_rust_src(branch: str, force: bool):
    rust_repo_git = "https://github.com/rust-lang/rust.git"
    try:
        dest_dir = os.path.join(os.path.dirname(__file__), "rust")

        # check if the existing repo already exist
        head_file = os.path.join(dest_dir, ".git", "refs", "heads", branch)
        if not force and os.path.isfile(head_file):
            # don't re-clone the same repo
            return
        if os.path.isdir(dest_dir):
            shutil.rmtree(dest_dir)

        args = ["git", "clone", "--depth", "1", rust_repo_git, dest_dir]
        if branch:
            args.extend(["-b", branch])
        subprocess.run(args).check_returncode()
    except PermissionError as pe:
        err(f"unable to remove `rust` directory due to lack of permission, try deleting it manually")
    except subprocess.SubprocessError as se:
        err(f"failed to clone rust repo: {se}")
    except Exception as ex:
        err(f"unknown exception caught when cloning rust repo: {ex}")


def gather_lint_info():
    pass


def clippy_lints_info():
    pass


def rustc_lints_info():
    pass


def cli() -> ArgumentParser:
    app = ArgumentParser(
        "Lint info extractor",
        usage="python3 run.py --branch <BRANCH/TAG>",
        description="Extract information of every rust lints from its repository"
    )
    app.add_argument(
        "-b", "--branch",
        action="store",
        help="Specify a branch or tag when pulling rust's repository"
    )
    app.add_argument(
        "--force",
        action="store_true",
        help="Force clone rust repository"
    )

    subcommands = app.add_subparsers(title="subcommands")

    clean = subcommands.add_parser("clean", help="Command to clean up files")
    clean.add_argument(
        "-a", "--all",
        action="store_true",
        help="clean up everything, including cloned rust repository"
    )

    return app


def main():
    ensure_cmd("git")

    args = cli().parse_args()

    clone_rust_src(args.branch, args.force)
    gather_lint_info()


if __name__ == "__main__":
    main()
