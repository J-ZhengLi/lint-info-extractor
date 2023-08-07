import mistune

class ClippyDocRenderer(mistune.HTMLRenderer):
    """
    Adjust the syntax of clippy lints doc
    """
    def paragraph(self, text):
        # why can't the doc syntax be strickly ruled, FFS!
        # Why am I doing this!
        # HELP! I'm losing it
        # I NEED to find a better way... OR DO I?
        if not text.endswith(":"):
            return super().paragraph(text)
        lower_text = text.lower()
        could_be_correct_example = False
        for keyword in [
            "instead",
            "be written",
            "would be",
            "you must",
        ]:
            if keyword in lower_text:
                could_be_correct_example = True

        if could_be_correct_example or lower_text in ["better:", "after:"]:
            return "<h3>Instead</h3>\n"
        return super().paragraph(text)


    def heading(self, text: str, level: int, **attrs) -> str:
        if text == "What it does":
            return "<h3>Summary</h3>\n"
        if "Why" in text:
            return "<h3>Explanation</h3>\n"
        if "Example" in text:
            return "<h3>Example</h3>\n"
        return super().heading(text, level, **attrs)
    

    def block_code(self, code: str, info=None) -> str:
        # Some clippy lint doc using a comment to indicate the correct usage,
        # instead of a `### Instead` header, idk why... Therefore they need to be splitted
        splitter = ""
        for comment_spliter_keywords in [ "should be", "can be" ]:
            for line in code.splitlines():
                if line.startswith("//") and comment_spliter_keywords in line:
                    splitter = line
                    break
        if splitter:
            splited_code = code.split(splitter, 1)
            content = "{}<h3>Instead</h3>\n{}".format(
                super().block_code(splited_code[0], info),
                super().block_code(splited_code[1], info)
            )
            return content
        else:
            return super().block_code(code, info)


class RustcDocRenderer(mistune.HTMLRenderer):
    """
    Adjust the syntax of rustc lints doc
    """
    def paragraph(self, text: str) -> str:
        if text == "{{produces}}":
            return ""
        return super().paragraph(text)
    

    def heading(self, text: str, level: int, **attrs) -> str:
        if "Example" in text:
            return "<h3>Example</h3>\n"
        return super().heading(text, level, **attrs)

