"""The grammars' node types mapped to neutral kinds, and the language facts the neutral calls read; types appear only here."""
from __future__ import annotations

IDENTIFIER, THIS, SUPER, CALL, NEW, MEMBER, LITERAL, ARRAY_LITERAL, ARRAY_NEW, CAST = (
    "identifier", "this", "super", "call", "new", "member", "literal", "array_literal", "array_new", "cast")
WRAPPING, FLOW, BLOCK, METHOD, CLASS_BODY, LAMBDA, OTHER = (
    "wrapping", "flow", "block", "method", "class_body", "lambda", "other")
LOCAL_DECLARATION, FIELD_DECLARATION, PROPERTY_DECLARATION, DECLARATOR, ASSIGNMENT, RETURN, ARGUMENTS, ARGUMENT = (
    "local_declaration", "field_declaration", "property_declaration", "declarator", "assignment", "return", "arguments", "argument")
EXPRESSION_STATEMENT, FUNCTION_BODY, PROPERTY_DELEGATE, CONTAINER = (
    "expression_statement", "function_body", "property_delegate", "container")

_TYPES = {
    IDENTIFIER: ("identifier",),
    THIS: ("this", "this_expression"),
    SUPER: ("super", "super_expression"),
    CALL: ("method_invocation", "call_expression"),
    NEW: ("object_creation_expression",),
    MEMBER: ("field_access", "navigation_expression"),
    LITERAL: ("string_literal", "decimal_integer_literal", "hex_integer_literal", "number_literal", "true", "false",
              "null_literal", "character_literal", "boolean_literal", "multiline_string_literal", "integer_literal"),
    ARRAY_LITERAL: ("array_initializer",),
    ARRAY_NEW: ("array_creation_expression",),
    CAST: ("cast_expression", "as_expression"),
    WRAPPING: ("parenthesized_expression", "postfix_expression", "non_null_assertion", "unary_expression"),
    FLOW: ("ternary_expression", "if_expression", "when_expression", "when_entry", "try_expression", "catch_block",
           "control_structure_body", "try_statement", "catch_clause", "finally_block", "binary_expression",
           "elvis_expression", "switch_expression", "switch_block", "switch_block_statement_group", "switch_rule",
           "labeled_statement", "if_statement", "synchronized_statement"),
    BLOCK: ("block", "statements", "constructor_body"),
    METHOD: ("method_declaration", "constructor_declaration", "compact_constructor_declaration", "static_initializer",
             "function_declaration", "secondary_constructor", "anonymous_initializer", "getter", "setter",
             "anonymous_function"),
    CLASS_BODY: ("class_body", "enum_class_body", "enum_body", "interface_body", "annotation_type_body", "record_body",
                 "source_file", "program", "enum_body_declarations"),
    LAMBDA: ("lambda_expression", "lambda_literal", "annotated_lambda"),
    LOCAL_DECLARATION: ("local_variable_declaration",),
    FIELD_DECLARATION: ("field_declaration", "constant_declaration"),
    PROPERTY_DECLARATION: ("property_declaration",),
    DECLARATOR: ("variable_declarator",),
    ASSIGNMENT: ("assignment_expression", "assignment"),
    RETURN: ("return_statement", "return_expression"),
    ARGUMENTS: ("argument_list", "value_arguments"),
    ARGUMENT: ("value_argument",),
    EXPRESSION_STATEMENT: ("expression_statement",),
    FUNCTION_BODY: ("function_body",),
    PROPERTY_DELEGATE: ("property_delegate",),
    CONTAINER: ("collection_literal",),
}
_KIND = {t: kind for kind, types in _TYPES.items() for t in types}

# operands joined into one value: none of them alone supplies it
JOINS = frozenset(("binary_expression",))
COMMENTS = frozenset(("line_comment", "block_comment", "multiline_comment", "comment"))
PRIMARY_CONSTRUCTOR, CLASS_PARAMETER = "primary_constructor", "class_parameter"
COMPANION = "companion_object"
VARIABLE_DECLARATION, MULTI_VARIABLE_DECLARATION = "variable_declaration", "multi_variable_declaration"
PARAMETER_LISTS = frozenset(("formal_parameters", "function_value_parameters"))
PARAMETERS = frozenset(("formal_parameter", "parameter"))
SPREAD_PARAMETER = "spread_parameter"
BINDING_SCOPES = frozenset(("for_statement", "enhanced_for_statement", "try_with_resources_statement", "catch_clause",
                            "catch_block", "lambda_expression", "lambda_literal"))
BINDING_NODES = frozenset(("variable_declarator", "resource", "formal_parameter", "catch_formal_parameter",
                           "inferred_parameters", "lambda_parameters", "variable_declaration"))
LAMBDA_PARAMETERS, LAMBDA_EXPRESSION, LAMBDA_LITERAL, ANNOTATED_LAMBDA = (
    "lambda_parameters", "lambda_expression", "lambda_literal", "annotated_lambda")
TYPES = frozenset(("type_identifier", "generic_type", "user_type", "nullable_type", "scoped_type_identifier", "array_type",
                   "integral_type"))
KOTLIN_CLASS = "class_declaration"
NAMED_ROOTS = frozenset(("constructor_declaration", "secondary_constructor", "static_initializer", "anonymous_initializer",
                         "getter", "setter", "anonymous_function", "compact_constructor_declaration"))
BODIES = frozenset(("block", "function_body", "constructor_body"))

# scope functions: the object is the lambda's implicit receiver or its `it`; some hand the object on, some the lambda's value
IMPLICIT_RECEIVER = frozenset(("apply", "run", "with"))
RETURNS_RECEIVER = frozenset(("apply", "also"))
SCOPE_FUNCTIONS = frozenset(("apply", "also", "run", "let", "with"))
# inline: their lambda runs before the call returns, so nothing in it is deferred
INLINE_CALLS = SCOPE_FUNCTIONS | frozenset(("use", "synchronized", "runCatching", "takeIf", "takeUnless", "forEach",
                                            "map", "repeat", "getOrPut", "computeIfAbsent", "withLock"))
# the lambda's last value is the call's value
VALUE_CALLS = frozenset(("lazy", "run", "synchronized", "runCatching", "withContext", "remember", "let", "apply", "also",
                         "with", "getOrPut", "computeIfAbsent", "use"))


def kind_of(node_type: str) -> str:
    return _KIND.get(node_type, OTHER)
