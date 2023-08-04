import unittest
import run
import utils

class TestLintExtraction(unittest.TestCase):
    def test_extract_clippy_lint_info(self):
        text = """
declare_clippy_lint! {
    /// ### What it does
    /// Checks for casts of function pointers to something other than usize
    ///
    /// ### Why is this bad?
    /// Casting a function pointer to anything other than usize/isize is not portable across
    /// architectures, because you end up losing bits if the target type is too small or end up with a
    /// bunch of extra bits that waste space and add more instructions to the final binary than
    /// strictly necessary for the problem
    ///
    /// Casting to isize also doesn't make sense since there are no signed addresses.
    ///
    /// ### Example
    /// ```rust
    /// fn fun() -> i32 { 1 }
    /// let _ = fun as i64;
    /// ```
    ///
    /// Use instead:
    /// ```rust
    /// # fn fun() -> i32 { 1 }
    /// let _ = fun as usize;
    /// ```
    #[clippy::version = "pre 1.29.0"]
    pub FN_TO_NUMERIC_CAST,
    style,
    "casting a function pointer to a numeric type other than usize"
}

pub fn foo() {
    let a = 1 + 1;
}

declare_clippy_lint! {
    /// ### What it does
    /// Checks for casts of a function pointer to a numeric type not wide enough to
    /// store address.
    ///
    /// ### Why is this bad?
    /// Such a cast discards some bits of the function's address. If this is intended, it would be more
    /// clearly expressed by casting to usize first, then casting the usize to the intended type (with
    /// a comment) to perform the truncation.
    ///
    /// ### Example
    /// ```rust
    /// fn fn1() -> i16 {
    ///     1
    /// };
    /// let _ = fn1 as i32;
    /// ```
    ///
    /// Use instead:
    /// ```rust
    /// // Cast to usize first, then comment with the reason for the truncation
    /// fn fn1() -> i16 {
    ///     1
    /// };
    /// let fn_ptr = fn1 as usize;
    /// let fn_ptr_truncated = fn_ptr as i32;
    /// ```
    #[clippy::version = "pre 1.29.0"]
    pub FN_TO_NUMERIC_CAST_WITH_TRUNCATION,
    style,
    "casting a function pointer to a numeric type not wide enough to store the address"
}
"""
        res = run.extract_lint_doc_and_name(text, "declare_clippy_lint!")
        self.assertEqual(
            res,
            [
                (
                    """### What it does
Checks for casts of function pointers to something other than usize

### Why is this bad?
Casting a function pointer to anything other than usize/isize is not portable across
architectures, because you end up losing bits if the target type is too small or end up with a
bunch of extra bits that waste space and add more instructions to the final binary than
strictly necessary for the problem

Casting to isize also doesn't make sense since there are no signed addresses.

### Example
```rust
fn fun() -> i32 { 1 }
let _ = fun as i64;
```

Use instead:
```rust
# fn fun() -> i32 { 1 }
let _ = fun as usize;
```""",
                "fn_to_numeric_cast"
                ),
                (
                    """### What it does
Checks for casts of a function pointer to a numeric type not wide enough to
store address.

### Why is this bad?
Such a cast discards some bits of the function's address. If this is intended, it would be more
clearly expressed by casting to usize first, then casting the usize to the intended type (with
a comment) to perform the truncation.

### Example
```rust
fn fn1() -> i16 {
    1
};
let _ = fn1 as i32;
```

Use instead:
```rust
// Cast to usize first, then comment with the reason for the truncation
fn fn1() -> i16 {
    1
};
let fn_ptr = fn1 as usize;
let fn_ptr_truncated = fn_ptr as i32;
```""",
                "fn_to_numeric_cast_with_truncation"
                )
            ]
        )


    def test_extract_rustc_lint_info(self):
        text = """
declare_lint! {
    /// The `text_direction_codepoint_in_comment` lint detects Unicode codepoints in comments that
    /// change the visual representation of text on screen in a way that does not correspond to
    /// their on memory representation.
    ///
    /// ### Example
    ///
    /// ```rust,compile_fail
    /// #![deny(text_direction_codepoint_in_comment)]
    /// fn main() {
    ///     println!("{:?}"); // '‮');
    /// }
    /// ```
    ///
    /// {{produces}}
    ///
    /// ### Explanation
    ///
    /// Unicode allows changing the visual flow of text on screen in order to support scripts that
    /// are written right-to-left, but a specially crafted comment can make code that will be
    /// compiled appear to be part of a comment, depending on the software used to read the code.
    /// To avoid potential problems or confusion, such as in CVE-2021-42574, by default we deny
    /// their use.
    pub TEXT_DIRECTION_CODEPOINT_IN_COMMENT,
    Deny,
    "invisible directionality-changing codepoints in comment"
}"""
        res = run.extract_lint_doc_and_name(text, "declare_lint!")
        self.assertEqual(
            res,
            [
                (
                    """The `text_direction_codepoint_in_comment` lint detects Unicode codepoints in comments that
change the visual representation of text on screen in a way that does not correspond to
their on memory representation.

### Example

```rust,compile_fail
#![deny(text_direction_codepoint_in_comment)]
fn main() {
    println!("{:?}"); // '‮');
}
```

{{produces}}

### Explanation

Unicode allows changing the visual flow of text on screen in order to support scripts that
are written right-to-left, but a specially crafted comment can make code that will be
compiled appear to be part of a comment, depending on the software used to read the code.
To avoid potential problems or confusion, such as in CVE-2021-42574, by default we deny
their use.""",
                    "text_direction_codepoint_in_comment"
                )
            ]
        )


    def test_parse_clippy_doc(self):
        doc_raw = """### What it does
Checks for casts of function pointers to something other than usize

### Why is this bad?
Casting a function pointer to anything other than usize/isize is not portable across
architectures, because you end up losing bits if the target type is too small or end up with a
bunch of extra bits that waste space and add more instructions to the final binary than
strictly necessary for the problem

Casting to isize also doesn't make sense since there are no signed addresses.

### Example
```rust
fn fun() -> i32 { 1 }
let _ = fun as i64;
```

Use instead:

```rust
# fn fun() -> i32 { 1 }
let _ = fun as usize;
```"""

        lint_name = "fn_to_numeric_cast"
        info = run.parse_clippy_lint_info(doc_raw, lint_name)
        self.assertEqual(info.name, lint_name)
        self.assertEqual(info.summary, "Checks for casts of function pointers to something other than usize")
        self.assertEqual(info.explanation, """Casting a function pointer to anything other than usize/isize is not portable across
architectures, because you end up losing bits if the target type is too small or end up with a
bunch of extra bits that waste space and add more instructions to the final binary than
strictly necessary for the problem
Casting to isize also doesn't make sense since there are no signed addresses.""")
        self.assertEqual(info.example, """fn fun() -> i32 { 1 }
let _ = fun as i64;""")
        self.assertEqual(info.instead, """# fn fun() -> i32 { 1 }
let _ = fun as usize;""")


    def test_translation(self):
        text = """It's basically guaranteed to be undefined behavior.
`UnsafeCell` is the only way to obtain aliasable data that is considered"""

        translator = utils.Translator("baidu", "zh")
        translated = translator.translate(text)
        self.assertEqual(translated, """它基本上保证是未定义的行为。
`UnsafeCell `是获得所考虑的可混叠数据的唯一方法""")


if __name__ == "__main__":
    unittest.main()

