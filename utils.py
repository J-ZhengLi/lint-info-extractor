import shutil
import os
import sys

import translators

def err(*msg: str, code=1, separator=" "):
    print("\x1b[31;1merror\x1b[0m: {}".format(f"{separator}".join(msg)), file=sys.stderr)
    exit(code)


def ensure_cmd(cmd: str):
    if shutil.which(cmd) is None:
        err(f"missing command '{cmd}', make sure it has been installed and added to PATH")


def ensure_path(path: str, ext_msg=""):
    if not os.path.exists(path):
        err("path does not exist,", ext_msg)


class Translator:
    def __init__(self, provider: str, lang: str, use_cache=False):
        self.provider = provider
        self.lang = lang
        if use_cache:
            _ = translators.preaccelerate_and_speedtest()


    def translate(self, text) -> str:
        try:
            return translators.translate_text(
                text,
                translator=self.provider,
                from_language="en",
                to_language=self.lang
            )
        except Exception as e:
            err(f"unknown exception caught when translating text: {e}")

