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
"""
        res = run.extract_lint_info_detail(text, True)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].name, "clippy::fn_to_numeric_cast")
        self.assertEqual(res[0].summary, "Checks for casts of function pointers to something other than usize")
        self.assertEqual(res[0].example, "fn fun() -> i32 { 1 }\nlet _ = fun as i64;")
        self.assertEqual(res[0].instead, "# fn fun() -> i32 { 1 }\nlet _ = fun as usize;")
        self.assertEqual(res[0].explanation, """Casting a function pointer to anything other than usize/isize is not portable across
architectures, because you end up losing bits if the target type is too small or end up with a
bunch of extra bits that waste space and add more instructions to the final binary than
strictly necessary for the problem
Casting to isize also doesn't make sense since there are no signed addresses.""")


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
        res = run.extract_lint_info_detail(text, False)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].name, "text_direction_codepoint_in_comment")
        self.assertEqual(res[0].summary, """The text_direction_codepoint_in_comment lint detects Unicode codepoints in comments that
change the visual representation of text on screen in a way that does not correspond to
their on memory representation.""")
        self.assertEqual(res[0].example, """#![deny(text_direction_codepoint_in_comment)]
fn main() {
    println!("{:?}"); // '‮');
}""")
        self.assertEqual(res[0].instead, "")
        self.assertEqual(res[0].explanation, """Unicode allows changing the visual flow of text on screen in order to support scripts that
are written right-to-left, but a specially crafted comment can make code that will be
compiled appear to be part of a comment, depending on the software used to read the code.
To avoid potential problems or confusion, such as in CVE-2021-42574, by default we deny
their use.""")


    def test_parse_clippy_doc(self):
        doc_raw = """### What it does
Checks for transmutes from a float to an integer.

### Why is this bad?
Transmutes are dangerous and error-prone, whereas `to_bits` is intuitive
and safe.

### Example
```rust
unsafe {
    let _: u32 = std::mem::transmute(1f32);
}

// should be:
let _: u32 = 1f32.to_bits();
```"""

        lint_name = "transmute_float_to_int"
        info = run.parse_lint_info(doc_raw, lint_name, True)
        self.assertEqual(info.name, lint_name)
        self.assertEqual(info.summary, "Checks for transmutes from a float to an integer.")
        self.assertEqual(info.explanation, """Transmutes are dangerous and error-prone, whereas to_bits is intuitive
and safe.""")
        self.assertEqual(info.example, """unsafe {
    let _: u32 = std::mem::transmute(1f32);
}""")
        self.assertEqual(info.instead, "let _: u32 = 1f32.to_bits();")


    def test_translation(self):
        text = """It's basically guaranteed to be undefined behavior.
`UnsafeCell` is the only way to obtain aliasable data that is considered"""

        translator = utils.Translator("baidu", "zh")
        translated = translator.translate(text)
        self.assertEqual(translated, """它基本上保证是未定义的行为。
`UnsafeCell `是获得所考虑的可混叠数据的唯一方法""")
        

    def test_translation_skip(self):
        whitelist = ["crate", "lint", "assert!"]
        text = "this is a lint that checks assert! usage in every crate"
        trans = utils.Translator("baidu", "zh", whitelist=whitelist)
        translated = trans.translate(text)
        # its not perfect, but it works
        self.assertEqual(translated, "这是一个lint，它检查每个crate中的assert！使用情况")


    def test_former_name_extraction(self):
        name_map = run.get_lints_former_name()
        self.assertEqual(
            str(name_map),
            """{'clippy::almost_complete_range': ['clippy::almost_complete_letter_range'], 'clippy::disallowed_names': ['clippy::blacklisted_name'], 'clippy::blocks_in_if_conditions': ['clippy::block_in_if_condition_expr', 'clippy::block_in_if_condition_stmt'], 'clippy::box_collection': ['clippy::box_vec'], 'clippy::redundant_static_lifetimes': ['clippy::const_static_lifetime'], 'clippy::cognitive_complexity': ['clippy::cyclomatic_complexity'], 'clippy::derived_hash_with_manual_eq': ['clippy::derive_hash_xor_eq'], 'clippy::disallowed_methods': ['clippy::disallowed_method'], 'clippy::disallowed_types': ['clippy::disallowed_type'], 'clippy::mixed_read_write_in_expression': ['clippy::eval_order_dependence'], 'clippy::useless_conversion': ['clippy::identity_conversion'], 'clippy::match_result_ok': ['clippy::if_let_some_result'], 'clippy::arithmetic_side_effects': ['clippy::integer_arithmetic'], 'clippy::overly_complex_bool_expr': ['clippy::logic_bug'], 'clippy::new_without_default': ['clippy::new_without_default_derive'], 'clippy::bind_instead_of_map': ['clippy::option_and_then_some'], 'clippy::expect_used': ['clippy::option_expect_used', 'clippy::result_expect_used'], 'clippy::map_unwrap_or': ['clippy::option_map_unwrap_or', 'clippy::option_map_unwrap_or_else', 'clippy::result_map_unwrap_or_else'], 'clippy::unwrap_used': ['clippy::option_unwrap_used', 'clippy::result_unwrap_used'], 'clippy::needless_borrow': ['clippy::ref_in_deref'], 'clippy::single_char_add_str': ['clippy::single_char_push_str'], 'clippy::module_name_repetitions': ['clippy::stutter'], 'clippy::recursive_format_impl': ['clippy::to_string_in_display'], 'clippy::invisible_characters': ['clippy::zero_width_space'], 'suspicious_double_ref_op': ['clippy::clone_double_ref'], 'drop_bounds': ['clippy::drop_bounds'], 'dropping_copy_types': ['clippy::drop_copy'], 'dropping_references': ['clippy::drop_ref'], 'for_loops_over_fallibles': ['clippy::for_loop_over_option', 'clippy::for_loop_over_result', 'clippy::for_loops_over_fallibles'], 'forgetting_copy_types': ['clippy::forget_copy'], 'forgetting_references': ['clippy::forget_ref'], 'array_into_iter': ['clippy::into_iter_on_array'], 'invalid_atomic_ordering': ['clippy::invalid_atomic_ordering'], 'invalid_value': ['clippy::invalid_ref'], 'let_underscore_drop': ['clippy::let_underscore_drop'], 'enum_intrinsics_non_enums': ['clippy::mem_discriminant_non_enum'], 'non_fmt_panics': ['clippy::panic_params'], 'named_arguments_used_positionally': ['clippy::positional_named_format_parameters'], 'temporary_cstring_as_ptr': ['clippy::temporary_cstring_as_ptr'], 'unknown_lints': ['clippy::unknown_clippy_lints'], 'unused_labels': ['clippy::unused_label']}"""
        )


if __name__ == "__main__":
    unittest.main()

