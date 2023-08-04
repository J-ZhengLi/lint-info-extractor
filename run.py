
import subprocess
import shutil
import os
from argparse import ArgumentParser
from pathlib import Path

import mistune
from bs4 import BeautifulSoup

from renderers import ClippyDocRenderer
from utils import err, ensure_cmd, ensure_path

class LintInfo:
    def __init__(self, lang: str, rust_dir=None, content=[]):
        self.lang = lang
        self.rust_dir = rust_dir
        self.content = content


    def clone_rust_src(self, branch: str, force: bool):
        rust_repo_git = "https://github.com/rust-lang/rust.git"
        try:
            # check if the existing repo already exist
            head_file = os.path.join(self.rust_dir, ".git", "refs", "heads", branch)
            if not force and os.path.isfile(head_file):
                # don't re-clone the same repo
                return
            if os.path.isdir(self.rust_dir):
                shutil.rmtree(self.rust_dir)

            args = ["git", "clone", "--depth", "1", rust_repo_git, self.rust_dir]
            if branch:
                args.extend(["-b", branch])
            subprocess.run(args).check_returncode()
        except PermissionError as pe:
            err(f"unable to remove `rust` directory due to lack of permission, try deleting it manually")
        except subprocess.SubprocessError as se:
            err(f"failed to clone rust repo: {se}")
        except Exception as ex:
            err(f"unknown exception caught when cloning rust repo: {ex}")


    def gather_lint_info(self):
        self.clippy_lints_info()
        pass


    def clippy_lints_info(self):
        """
        Retrive all clippy lints information.

        clippy lints declaration typically resides under `rust/src/tools/clippy/clippy_lints/src`,
        all its left to do is (maybe) entering that directory and look for
        `declare_clippy_lint!` blocks, then extracting the doc comment as markdown docs,
        along with the lint name after the doc.
        """
        clippy_lints_path = os.path.join(
            self.rust_dir,
            "src", "tools", "clippy", "clippy_lints", "src"
        )
        ensure_path(clippy_lints_path, "the rust source code might be corrupted")
        rs_files = Path(clippy_lints_path).glob("**/*.rs")

        try:
            for file in rs_files:
                print(file)
        except Exception as ex:
            err(f"unknown exception caught during fetching clippy lints info: {ex}")


    def rustc_lints_info(self):
        pass


class LintInfoDetail:
    def __init__(self, name: str, summary: str, example: str, instead: str, explanation: str):
        self.name = name
        self.summary = summary
        self.example = example
        self.instead = instead
        self.explanation = explanation


def extract_lint_doc_and_name(text: str, start: str) -> (str, str):
    res = []
    extraction_started = False
    doc_list = []
    lint_name = ""
    for line in text.split("\n"):
        trimmed = line.strip()
        if not trimmed:
            continue
        if trimmed.startswith(start):
            extraction_started = True
        elif extraction_started and trimmed.startswith("}"):
            extraction_started = False
            res.append(("\n".join(doc_list), lint_name.lower()))
            doc_list = []
            lint_name = ""
        elif extraction_started and trimmed.startswith("///"):
            if len(trimmed) == 3:
                doc_list.append("")
            else:
                doc_list.append(trimmed.removeprefix("/// "))
        elif extraction_started:
            maybe_lint_name = trimmed.lstrip("pub ").rstrip(",")
            if maybe_lint_name.isupper():
                lint_name = maybe_lint_name
    return res


def parse_clippy_lint_info(doc: str, lint_name: str) -> LintInfoDetail:
    html = mistune.markdown(doc, renderer=ClippyDocRenderer())
    soup = BeautifulSoup(html, features="html.parser")

    # temp dict to store text after each corresponding header
    res = dict()

    for heading in soup.find_all("h3"):
        text = ""
        if heading.text not in ["Summary", "Explanation", "Example", "Instead"]:
            continue
        for sib in heading.next_siblings:
            if sib.name == "h3":
                break
            text += sib.text
        res[heading.text] = text.strip()
    
    try:
        return LintInfoDetail(
            lint_name,
            res["Summary"],
            res["Example"],
            res["Instead"],
            res["Explanation"]
        )
    except KeyError as ke:
        err(f"failed to parse clippy lint info from html: {ke}")


def cli() -> ArgumentParser:
    app = ArgumentParser(
        "Lint info extractor",
        usage="python3 run.py --branch <BRANCH/TAG>",
        description="Extract information of every rust lints from its repository"
    )
    app.add_argument(
        "-b", "--branch",
        action="store",
        help="Specify a branch or tag when cloning rust"
    )
    app.add_argument(
        "--force",
        action="store_true",
        help="Force clone rust repository"
    )
    app.add_argument(
        "--lang",
        action="store",
        help="Specify a language to translate for output. \
            Note this only affects lint's description, and the result of translation might \
            be incorrect."
    )
    app.add_argument(
        "--translator",
        action="store",
        help="Specify a translation service provider",
        default="baidu",
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

    dest_rust_dir = os.path.join(os.path.dirname(__file__), "rust")
    info = LintInfo(args.lang, rust_dir=dest_rust_dir)

    info.clone_rust_src(args.branch, args.force)
    info.gather_lint_info()


if __name__ == "__main__":
    main()
