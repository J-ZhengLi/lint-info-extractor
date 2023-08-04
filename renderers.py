import mistune

class ClippyDocRenderer(mistune.HTMLRenderer):
    """
    Re-arrange the syntax of clippy lints doc to match rustc lints doc
    """
    def paragraph(self, text):
        if text == "Use instead:":
            return "<h3>Instead</h3>\n"
        return super().paragraph(text)
    
    def heading(self, text: str, level: int, **attrs) -> str:
        if text == "What it does":
            return "<h3>Summary</h3>\n"
        if text == "Why is this bad?":
            return "<h3>Explanation</h3>\n"
        return super().heading(text, level, **attrs)


class RustcDocRenderer(mistune.HTMLRenderer):
    """
    Just to remove that `{{produces}}` noise from rustc lints doc :(
    
    Although, I could just use `str.replace`, but I think this might be more efficient
    """
    def paragraph(self, text: str) -> str:
        if text == "{{produces}}":
            return ""
        return super().paragraph(text)

