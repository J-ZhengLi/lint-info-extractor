
import subprocess
import shutil
import os
import pkg_resources
import re
from itertools import chain
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd
import mistune
from bs4 import BeautifulSoup

from renderers import ClippyDocRenderer, RustcDocRenderer
from utils import err, ensure_cmd, ensure_path, Translator, script_dir_with

class LintInfo:
    def __init__(self, lang: str, provider, rust_dir=None, content=[]):
        self.lang = lang
        self.translation_provider = provider
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
        except PermissionError:
            err("unable to remove `rust` directory due to lack of permission, try deleting it manually")
        except subprocess.SubprocessError as se:
            err(f"failed to clone rust repo: {se}")
        except Exception as ex:
            err(f"unknown exception caught when cloning rust repo: {ex}")


    def gather_lint_info(self):
        self.content += self.clippy_lints_info()
        self.content += self.rustc_lints_info()

        # translate if required
        if self.lang and self.lang.lower() != "en":
            cache_path = script_dir_with(
                "temp",
                ".translation_cache-{}-{}".format(self.translation_provider, self.lang)
            )
            whitelist = []
            try:
                with open(script_dir_with("example", "whitelist"), "r", encoding="utf8") as wf:
                    whitelist = set(wf.read().strip().split(","))
                translator = Translator(self.translation_provider, self.lang, whitelist=whitelist)
                cached_dict = dict()
                # load cache
                if os.path.isfile(cache_path):
                    with open(cache_path, "r", encoding="utf8") as cf:
                        for line in cf.readlines():
                            if not line:
                                continue
                            name, summary, desc = line.strip().split("@@@", 2)
                            cached_dict[name] = (summary, desc)
                # update cache
                with open(cache_path, "w", encoding="utf8") as cf:
                    for cont in self.content:
                        if cont.name in cached_dict:
                            print("using cached translation for lint '{}'".format(cont.name))
                            translated = cached_dict[cont.name]
                        else:
                            print("translating lint '{}'".format(cont.name))
                            summary = "" if not cont.summary else translator.translate(cont.summary.replace("\n", ""))
                            explanation = "" if not cont.explanation else translator.translate(cont.explanation.replace("\n", ""))
                            translated = (summary, explanation)
                        
                        cont.summary = translated[0]
                        cont.explanation = translated[1]
                        cf.write("{}@@@{}@@@{}\n".format(cont.name, translated[0], translated[1]))
            except IOError as ie:
                err(f"unable to translate lints info: {ie}")
            except Exception as ex:
                raise ex


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
        # filter out utils directory, which does not contain public lints
        rs_files = [
            f for f in Path(clippy_lints_path).glob("**/*.rs")
            if "utils" not in os.path.dirname(f)
        ]
        info_details = []
        for file in rs_files:
            info_details += _lint_info_from_file_(file, True)
        
        return info_details


    def rustc_lints_info(self):
        """
        Retrive all rustc lints information.

        rustc lints declaration stores under two different locations:
        - `rust/compiler/rustc_lint/src`
        - `rust/compiler/rustc_lint_defs/src`
        all its left to do is (maybe) entering these directories and look for
        `declare_lint!` blocks, then extracting the doc comment as markdown docs,
        along with the lint name after the doc.
        """
        lints_path_a = os.path.join(self.rust_dir, "compiler", "rustc_lint", "src")
        lints_path_b = os.path.join(self.rust_dir, "compiler", "rustc_lint_defs", "src")
        ensure_path(lints_path_a, "the rust source code might be corrupted")
        ensure_path(lints_path_b, "the rust source code might be corrupted")
        rs_files = chain(Path(lints_path_a).glob("**/*.rs"), Path(lints_path_b).glob("**/*.rs"))
        info_details = []
        for file in rs_files:
            info_details += _lint_info_from_file_(file, False)
        return info_details
    

    def export(self, path: str):
        _, ext = os.path.splitext(path)
        if ext == ".xlsx":
            # convert self.content from list to dict
            data = {
                "Lint": [],
                "Former Name": [],
                "Summary": [],
                "Explanation": [],
                "Example": [],
                "How to fix": [],
            }
            try:
                for det in self.content:
                    data["Lint"].append(det.name)
                    data["Former Name"].append("\n".join(det.former_name))
                    data["Summary"].append(det.summary)
                    data["Explanation"].append(det.explanation)
                    data["Example"].append(det.example)
                    data["How to fix"].append(det.instead)

                df = pd.DataFrame(data)
                if "jinja2" in {pkg.key for pkg in pkg_resources.working_set}:
                    print("applying dataframe styling")
                    df.style.set_properties(**{'text-align': 'left'})
                df.to_excel(path, sheet_name="all lints")
            except KeyError as ke:
                err(f"failed to convert lint data into dictionary: {ke}")
            except IOError as io:
                err(f"failed to write result: {io}")
            except Exception as ex:
                err(f"unknown error caught when outputing result: {ex}")
        else:
            err("unsupported output format:", ext)


def _lint_info_from_file_(file, is_clippy) -> list:
    try:
        details = []
        with open(file, "r", encoding="utf8") as sf:
            src_content = sf.read()
            details = extract_lint_info_detail(src_content, is_clippy)
        print("{} lints detected from '{}'".format(len(details), file))
        return details
    except Exception as ex:
        err(f"unknown error: {ex}")

class LintInfoDetail:
    def __init__(self, name: str, summary: str, example: str, instead: str, explanation: str, former_name: str):
        self.name = name
        self.summary = summary
        self.example = example
        self.instead = instead
        self.explanation = explanation
        self.former_name = former_name


def extract_lint_info_detail(text: str, is_clippy: bool) -> list:
    res = []
    extraction_started = False
    doc_list = [""]
    lint_name = ""
    start = "declare_clippy_lint!" if is_clippy else "declare_lint!"
    for line in text.split("\n"):
        trimmed = line.strip()
        if not trimmed:
            continue
        if trimmed.startswith(start):
            extraction_started = True
        elif extraction_started and trimmed.startswith("}"):
            extraction_started = False
            if len(doc_list) > 1 and doc_list[1] != "### What it does":
                doc_list[0] = "### Summary"
            # already have enough info we need for this lint, parse it then add to result
            doc = "\n".join(doc_list)
            name = lint_name.lower() if not is_clippy else "clippy::{}".format(lint_name.lower())
            info = parse_lint_info(doc, name, is_clippy)
            res.append(info)
            # reset searching parameters for next lint declared in the same file
            doc_list = [""]
            lint_name = ""
        elif extraction_started and trimmed.startswith("///"):
            if len(trimmed) == 3:
                doc_list.append("")
            else:
                doc_list.append(trimmed.removeprefix("/// "))
        elif extraction_started and not lint_name:
            maybe_lint_name = trimmed.split(" ")[-1].rstrip(",")
            if maybe_lint_name.isupper():
                lint_name = maybe_lint_name
    return res


def parse_lint_info(doc: str, lint_name: str, is_clippy: bool) -> LintInfoDetail:
    if is_clippy:
        html = mistune.markdown(doc, renderer=ClippyDocRenderer())
    else:
        html = mistune.markdown(doc, renderer=RustcDocRenderer())
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

    former_names = get_lints_former_name()
    
    return LintInfoDetail(
        lint_name,
        value_or_empty("Summary", res, lint_name),
        value_or_empty("Example", res, lint_name),
        value_or_empty("Instead", res, lint_name),
        value_or_empty("Explanation", res, lint_name),
        "" if lint_name not in former_names else former_names[lint_name]
    )


def get_lints_former_name() -> dict:
    """
    Get a dictionary of lint's current name as key, with its former name as value
    """
    # former names could be fetched from this file
    rename_lints_file = script_dir_with("rust", "src", "tools", "clippy", "clippy_lints", "src", "renamed_lints.rs")
    ensure_path(rename_lints_file)
    result = dict()
    cont = ""

    with open(rename_lints_file, "r", encoding="utf8") as cf:
        cont = cf.read()
    
    pat = r"\(\"(.*?)\", \"(.*?)\"\),"
    pairs = re.findall(pat, cont)
    for pair in pairs:
        if pair[1] in result:
            result[pair[1]].append(pair[0])
        else:
            result[pair[1]] = [pair[0]]
    return result


def value_or_empty(key: str, map: dict, name="") -> str:
    try:
        return map[key]
    except KeyError:
        if name:
            print("missing header '{}' for lint '{}'".format(key, name))
        return ""


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
        "--provider",
        action="store",
        help="Specify a translation service provider",
        default="baidu",
    )
    app.add_argument(
        "-o", "--output",
        action="store",
        help="Set a local path for result export",
        default="./result.xlsx"
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

    dest_rust_dir = script_dir_with("rust")
    temp_dir = script_dir_with("temp")
    if not os.path.isdir(temp_dir):
        os.makedirs(temp_dir)
    info = LintInfo(args.lang, provider=args.provider, rust_dir=dest_rust_dir)

    info.clone_rust_src(args.branch, args.force)
    info.gather_lint_info()
    info.export(args.output)


if __name__ == "__main__":
    main()
