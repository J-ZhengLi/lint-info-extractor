import shutil
import os
import sys
import re

import translators

def script_dir_with(*paths) -> str:
    return os.path.join(os.path.dirname(__file__), *paths)


def err(*msg: str, code=1, separator=" "):
    print("\x1b[31;1merror\x1b[0m: {}".format(f"{separator}".join(msg)), file=sys.stderr)
    exit(code)


def ensure_cmd(cmd: str):
    if shutil.which(cmd) is None:
        err(f"missing command '{cmd}', make sure it has been installed and added to PATH")


def ensure_path(path: str, ext_msg=""):
    if not os.path.exists(path):
        err(f"path specified at '{path}' does not exist,", ext_msg)


class Translator:
    def __init__(self, provider: str, lang: str, use_cache=False, whitelist={}):
        self.provider = provider
        self.lang = lang
        if use_cache:
            _ = translators.preaccelerate_and_speedtest()
        if type(whitelist) == set:
            self.whitelist = whitelist
        else:
            self.whitelist = set(whitelist)


    def translate(self, text: str) -> str:
        filtered = []
        # RIP performance
        for word in text.split(" "):
            if not word:
                continue
            if word in self.whitelist:
                filtered.append("[__{}]".format(word))
            else:
                filtered.append(word)
        filtered_text = " ".join(filtered)
        try:
            
            translated = translators.translate_text(
                filtered_text,
                translator=self.provider,
                from_language="en",
                to_language=self.lang,
                if_ignore_limit_of_length=True,
            )
            return re.sub(r"\[__([^\]]+)\]", r"\1", translated)
        except KeyError:
            print(f"failed to translate '{filtered_text}', returning the original string")
            return text
        except Exception as e:
            print(f"unknown exception caught when translating '{text}'")
            raise e

