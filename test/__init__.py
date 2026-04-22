# -*- coding: utf-8 -*-
# Copyright JS Foundation and other contributors, https://js.foundation/
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


import os
import re
import json
import glob
import fnmatch
import subprocess
import unittest

from esprima import parse, parseModule, tokenize, Error, toDict
from esprima.nodes import Script

BASE_DIR = os.path.dirname(__file__)

SOURCE_RE = re.compile(br'''^var\s+source\s*=\s*(['"])(.*)\1;\s*$''', re.DOTALL)

EXPECTED_FAULRES = (
    ('TestExpression', u'u_flag_surrogate_pair'),  # Regex comes with no value
)


def test_factory(_path):
    def test_file(filename):
        result_path = os.path.dirname(filename)
        result_syntax_path = os.path.join(result_path, 'syntax')
        if os.path.isdir(result_syntax_path):
            result_path = result_syntax_path
        result_base = os.path.join(result_path, os.path.basename(os.path.splitext(filename.replace('.source.', '.'))[0]))
        for result_type in ('', '.tree', '.tokens', '.failure'):
            result_file = '%s%s.json' % (result_base, result_type)
            if os.path.exists(result_file):
                if not result_type:
                    result_type = '.tree'
                break
        else:
            return

        def test(self):
            with open(result_file, 'rb') as f:
                expected_json = f.read()
            expected = toDict(json.loads(expected_json.decode('utf-8')))
            if isinstance(expected, dict):
                expected.pop('description', None)  # Not all json failure files include description
                expected.pop('tokenize', None)  # tokenize is not part of errors
                options = expected.pop('options', None)  # Extracts options from tree (if any)
            else:
                options = None

            with open(filename, 'rb') as f:
                actual_code = f.read()
            if '.source.' in filename:
                actual_code = SOURCE_RE.sub(rb'\2', actual_code).decode('unicode_escape')
            else:
                actual_code = actual_code.decode('utf-8')

            try:
                if result_type == '.tokens':
                    if options is None:
                        options = {
                            'loc': True,
                            'range': True,
                            'comment': True,
                            'tolerant': True,
                        }
                    actual = toDict(tokenize(actual_code, options=options))
                else:
                    sourceType = 'module' if '.module.' in filename else 'script'
                    if options is None:
                        options = {
                            'jsx': True,
                            'comment': 'comments' in expected,
                            'range': True,
                            'loc': True,
                            'tokens': True,
                            'raw': True,
                            'tolerant': 'errors' in expected,
                            'source': None,
                            'sourceType': expected.get('sourceType', sourceType),
                        }

                    if options.get('comment'):
                        def hasAttachedComment(expected):
                            for k, v in expected.items():
                                if k in ('leadingComments', 'trailingComments', 'innerComments'):
                                    return True
                                elif isinstance(v, dict):
                                    if hasAttachedComment(v):
                                        return True
                                elif isinstance(v, list):
                                    for i in v:
                                        if isinstance(i, dict):
                                            if hasAttachedComment(i):
                                                return True
                            return False
                        options['attachComment'] = hasAttachedComment(expected)

                    if expected.get('tokens'):
                        token = expected['tokens'][0]
                        options['range'] = 'range' in token
                        options['loc'] = 'loc' in token

                    if expected.get('comments'):
                        comment = expected['comments'][0]
                        options['range'] = 'range' in comment
                        options['loc'] = 'loc' in comment

                    if options.get('loc'):
                        options['source'] = expected.get('loc', {}).get('source')

                    actual = toDict(parse(actual_code, options=options))
            except Error as e:
                actual = e.toDict()

            self.assertEqual(expected, actual)

        test_name = os.path.basename(os.path.splitext(filename)[0])
        test_name = re.sub(r'[-. _]+', '_', test_name)
        if not test_name.isupper():
            test_name = re.sub(r'(?<=[^_])([A-Z])', r'_\1', test_name)
        test_name = test_name.lower()

        return test_name, test

    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for filename in files:
                if fnmatch.fnmatch(filename, '*.js'):
                    filename = os.path.join(root, filename)
                    test = test_file(filename)
                    if test:
                        yield test
    else:
        test = test_file(path)
        if test:
            yield test


class TestEsprima(unittest.TestCase):
    def test_basic(self):
        expected = {
            "sourceType": "script",
            "type": "Program",
            "body": [
                {
                    "type": "VariableDeclaration",
                    "declarations": [
                        {
                            "type": "VariableDeclarator",
                            "id": {
                                "type": "Identifier",
                                "name": "$"
                            },
                            "init": {
                                "type": "Literal",
                                "value": "Hello!",
                                "raw": '"Hello!"'
                            }
                        }
                    ],
                    "kind": "var"
                }
            ]
        }

        actual = toDict(parse('var $ = "Hello!"'))

        self.assertEqual(expected, actual)

    def test_recursion(self):
        script = ('var testcode = unescape(""+'
                  + '""+"%u8300"+"%u2f8d"+""+""+"%u8300"+"%u2f8d"+""+""+"%u8300"+"%u2f8d"+""+""+"%u8300"+' * 20
                  + '"");')
        r = parse(script)
        self.assertIsInstance(r, Script)

    def test_reinterpret_as_pattern_python_class(self):
        def arrow_param(src):
            return parse(src).body[0].expression.arguments[0].params[0]

        from esprima import nodes
        cases = [
            ("f(({x}) => x)",      nodes.ObjectPattern),
            ("f(([x]) => x)",      nodes.ArrayPattern),
            ("f(({x} = {}) => x)", nodes.AssignmentPattern),
            ("f((...x) => x)",     nodes.RestElement),
        ]
        for src, expected_class in cases:
            with self.subTest(src=src):
                node = arrow_param(src)
                self.assertIsInstance(node, expected_class)

    def test_bigint_literals(self):
        """Test BigInt literal parsing for all number bases"""
        # Test decimal BigInt
        result = toDict(parse('var x = 123n;'))
        literal = result['body'][0]['declarations'][0]['init']
        self.assertEqual(literal['type'], 'Literal')
        self.assertEqual(literal['value'], 123)
        self.assertEqual(literal['raw'], '123n')
        
        # Test hexadecimal BigInt
        result = toDict(parse('var x = 0x9e3779b185ebca87n;'))
        literal = result['body'][0]['declarations'][0]['init']
        self.assertEqual(literal['type'], 'Literal')
        self.assertEqual(literal['value'], 11400714785074694791)
        self.assertEqual(literal['raw'], '0x9e3779b185ebca87n')
        
        # Test binary BigInt
        result = toDict(parse('var x = 0b1010n;'))
        literal = result['body'][0]['declarations'][0]['init']
        self.assertEqual(literal['type'], 'Literal')
        self.assertEqual(literal['value'], 10)
        self.assertEqual(literal['raw'], '0b1010n')
        
        # Test octal BigInt
        result = toDict(parse('var x = 0o777n;'))
        literal = result['body'][0]['declarations'][0]['init']
        self.assertEqual(literal['type'], 'Literal')
        self.assertEqual(literal['value'], 511)
        self.assertEqual(literal['raw'], '0o777n')

    def test_nullish_coalescing(self):
        result = toDict(parse('var x = a ?? b;'))
        init = result['body'][0]['declarations'][0]['init']
        self.assertEqual(init['type'], 'LogicalExpression')
        self.assertEqual(init['operator'], '??')

        with self.assertRaises(Error):
            parse('a ?? b || c')
        with self.assertRaises(Error):
            parse('a && b ?? c')

        result = toDict(parse('(a ?? b) || c'))
        expr = result['body'][0]['expression']
        self.assertEqual(expr['type'], 'LogicalExpression')
        self.assertEqual(expr['operator'], '||')

    def test_optional_chaining(self):
        result = toDict(parse('a?.b.c'))
        expr = result['body'][0]['expression']
        self.assertEqual(expr['type'], 'ChainExpression')
        self.assertEqual(expr['expression']['type'], 'MemberExpression')
        self.assertFalse(expr['expression'].get('optional', False))
        self.assertTrue(expr['expression']['object']['optional'])

        result = toDict(parse('a?.()'))
        expr = result['body'][0]['expression']
        self.assertEqual(expr['type'], 'ChainExpression')
        self.assertEqual(expr['expression']['type'], 'CallExpression')
        self.assertTrue(expr['expression']['optional'])

        with self.assertRaises(Error):
            parse('a?.b.c = 1')

    def test_numeric_separators(self):
        cases = [
            ('var x = 1_000;', 1000),
            ('var x = 0xA_B;', 0xAB),
            ('var x = 0b1010_0001;', 0b10100001),
            ('var x = 0o7_7;', 0o77),
            ('var x = 1_2n;', 12),
            ('var x = 0xA_Bn;', 0xAB),
            ('var x = 0b1010_0001n;', 0b10100001),
            ('var x = 0o7_7n;', 0o77),
        ]
        for src, value in cases:
            with self.subTest(src=src):
                result = toDict(parse(src))
                literal = result['body'][0]['declarations'][0]['init']
                self.assertEqual(literal['value'], value)

        invalid_cases = [
            'var x = 0_1;',
            'var x = 1._0;',
            'var x = 0x_A;',
            'var x = 0b_1;',
            'var x = 0o_7;',
            'var x = 0123n;',
        ]
        for src in invalid_cases:
            with self.subTest(src=src):
                with self.assertRaises(Error):
                    parse(src)

    def test_computed_class_fields(self):
        result = toDict(parse('class A { [x] = 1; ["y"]; [z]\nw }'))
        elements = result['body'][0]['body']['body']
        self.assertEqual(elements[0]['type'], 'FieldDefinition')
        self.assertTrue(elements[0]['computed'])
        self.assertEqual(elements[0]['key']['name'], 'x')
        self.assertEqual(elements[0]['value']['value'], 1)
        self.assertEqual(elements[1]['type'], 'FieldDefinition')
        self.assertTrue(elements[1]['computed'])
        self.assertIsNone(elements[1].get('value'))
        self.assertEqual(elements[2]['type'], 'FieldDefinition')
        self.assertTrue(elements[2]['computed'])
        self.assertEqual(elements[3]['type'], 'FieldDefinition')
        self.assertEqual(elements[3]['key']['name'], 'w')

        invalid_cases = [
            'class C { [x] y }',
            'class C { "x" async(){} }',
            'class C { 1 [x] }',
            'class C { true async(){} }',
            'class C { [x] = 1 y }',
        ]
        for src in invalid_cases:
            with self.subTest(src=src):
                with self.assertRaises(Error):
                    parse(src)

    def test_async_class_elements(self):
        valid_fields = [
            'class C { async; }',
            'class C { async = 1; }',
            'class C { static async = 1; }',
        ]
        for src in valid_fields:
            with self.subTest(src=src):
                element = toDict(parse(src))['body'][0]['body']['body'][0]
                self.assertEqual(element['type'], 'FieldDefinition')
                self.assertEqual(element['key']['name'], 'async')

        valid_methods = [
            'class C { async x(){} }',
            'class C { async "x"(){} }',
            'class C { async [x](){} }',
            'class C { static async true(){} }',
        ]
        for src in valid_methods:
            with self.subTest(src=src):
                element = toDict(parse(src))['body'][0]['body']['body'][0]
                self.assertEqual(element['type'], 'MethodDefinition')
                self.assertTrue(element['value']['async'])

        invalid_cases = [
            'class C { async x; }',
            'class C { async "x"; }',
            'class C { async 1 = 2; }',
            'class C { async [x]; }',
            'class C { static async true; }',
        ]
        for src in invalid_cases:
            with self.subTest(src=src):
                with self.assertRaises(Error):
                    parse(src)

    def test_constructor_class_fields(self):
        invalid_cases = [
            'class C { constructor; }',
            'class C { constructor = 1; }',
            'class C { "constructor"; }',
            'class C { "constructor" = 1; }',
            'class C { static constructor; }',
            'class C { static constructor = 1; }',
            'class C { static "constructor"; }',
            'class C { static "constructor" = 1; }',
        ]
        for src in invalid_cases:
            with self.subTest(src=src):
                with self.assertRaises(Error):
                    parse(src)

        valid_cases = [
            'class C { constructor(){} }',
            'class C { "constructor"(){} }',
            'class C { static constructor(){} }',
            'class C { static "constructor"(){} }',
            'class C { ["constructor"]; }',
            'class C { static ["constructor"] = 1; }',
        ]
        for src in valid_cases:
            with self.subTest(src=src):
                parse(src)

    def test_ecma2025_import_attributes_on_exports(self):
        named = toDict(parseModule('export { foo } from "./data.json" with { type: "json" };'))
        declaration = named['body'][0]
        self.assertEqual(declaration['type'], 'ExportNamedDeclaration')
        self.assertEqual(declaration['source']['value'], './data.json')
        self.assertEqual(declaration['attributes'][0]['key']['name'], 'type')
        self.assertEqual(declaration['attributes'][0]['value']['value'], 'json')

        batch = toDict(parseModule('export * from "./data.json" with { type: "json" };'))
        declaration = batch['body'][0]
        self.assertEqual(declaration['type'], 'ExportAllDeclaration')
        self.assertEqual(declaration['source']['value'], './data.json')
        self.assertEqual(declaration['attributes'][0]['key']['name'], 'type')
        self.assertEqual(declaration['attributes'][0]['value']['value'], 'json')

        namespace = toDict(parseModule('export * as data from "./data.json" with { type: "json" };'))
        declaration = namespace['body'][0]
        self.assertEqual(declaration['type'], 'ExportAllDeclaration')
        self.assertEqual(declaration['exported']['name'], 'data')
        self.assertEqual(declaration['attributes'][0]['value']['value'], 'json')

        string_namespace = toDict(parseModule('export * as "data" from "./data.json";'))
        declaration = string_namespace['body'][0]
        self.assertEqual(declaration['type'], 'ExportAllDeclaration')
        self.assertEqual(declaration['exported']['type'], 'Literal')
        self.assertEqual(declaration['exported']['value'], 'data')

        string_exported_name = toDict(parseModule('const foo = 1; export { foo as "bar" };'))
        specifier = string_exported_name['body'][1]['specifiers'][0]
        self.assertEqual(specifier['local']['name'], 'foo')
        self.assertEqual(specifier['exported']['type'], 'Literal')
        self.assertEqual(specifier['exported']['value'], 'bar')

        string_local_reexport = toDict(parseModule('export { "foo" as bar } from "./m.js" with { type: "json" };'))
        declaration = string_local_reexport['body'][0]
        specifier = declaration['specifiers'][0]
        self.assertEqual(specifier['local']['type'], 'Literal')
        self.assertEqual(specifier['local']['value'], 'foo')
        self.assertEqual(specifier['exported']['name'], 'bar')
        self.assertEqual(declaration['attributes'][0]['key']['name'], 'type')

        string_named_reexport = toDict(parseModule('export { "foo" } from "./m.js";'))
        specifier = string_named_reexport['body'][0]['specifiers'][0]
        self.assertEqual(specifier['local']['value'], 'foo')
        self.assertEqual(specifier['exported']['value'], 'foo')

        keyword_attribute = toDict(parseModule('export * from "./data.json" with { default: "json" };'))
        declaration = keyword_attribute['body'][0]
        self.assertEqual(declaration['attributes'][0]['key']['name'], 'default')
        self.assertEqual(declaration['attributes'][0]['value']['value'], 'json')

        literal_attribute = toDict(parseModule('export * from "./data.json" with { "default": "json" };'))
        declaration = literal_attribute['body'][0]
        self.assertEqual(declaration['attributes'][0]['key']['value'], 'default')
        self.assertEqual(declaration['attributes'][0]['value']['value'], 'json')

        with self.assertRaises(Error):
            parseModule('import data from "./data.json" with { type: "json", type: "json" };')

        with self.assertRaises(Error):
            parseModule('import data from "./data.json" with { default: "json", "default": "json" };')

        with self.assertRaises(Error):
            parseModule('export { "foo" };')

    def test_ecma2025_regexp_named_groups_and_modifiers(self):
        literal = toDict(parse(r'/(?<year>\d{4})-\k<year>/;'))['body'][0]['expression']
        self.assertEqual(literal['type'], 'Literal')
        self.assertEqual(literal['regex']['pattern'], r'(?<year>\d{4})-\k<year>')

        escaped_name = toDict(parse(r'/(?<\u0061>a)\k<a>/;'))['body'][0]['expression']
        self.assertEqual(escaped_name['type'], 'Literal')
        self.assertEqual(escaped_name['regex']['pattern'], r'(?<\u0061>a)\k<a>')

        duplicate = toDict(parse(r'/(?<year>\d{4})-\d{2}|\d{2}-(?<year>\d{4})/;'))['body'][0]['expression']
        self.assertEqual(duplicate['regex']['pattern'], r'(?<year>\d{4})-\d{2}|\d{2}-(?<year>\d{4})')

        modifier_cases = [
            r'/(?i:abc)/;',
            r'/(?i-:abc)/;',
            r'/(?-i:abc)/i;',
            r'/(?s-m:abc)/m;',
            r'/(?<x>a)\cA/u;',
            r'/\cA/u;',
            r'/(?<\u{10400}>a)\k<\u{10400}>/u;',
            r'/(?<\u{10400}>a)\k<\u{10400}>/v;',
            r'/(?<a\u{10400}>x)/u;',
            r'/(?<a\u{10400}>x)/v;',
            r'/(?<\uD801\uDC00>x)/u;',
            r'/(?<\uD801\uDC00>x)/v;',
            r'/(?<a\uD801\uDC00>x)/u;',
            r'/(?<\u{10400}>x)/;',
            r'/(?<a\u{10400}>x)/;',
            r'/(?<a\u{1D7CE}>a)/u;',
            r'/(?<a\u200c>a)/u;',
            r'/(?<=\d+)/u;',
            r'/(?<=\d+)/v;',
            r'/(?<=\p{RGI_Emoji}*)/v;',
            r'/\1(a)/u;',
            r'/\1(a)/v;',
            r'/\2(a)(b)/u;',
            r'/\10(a)(b)(c)(d)(e)(f)(g)(h)(i)(j)/u;',
            r'/(a)\1/u;',
            r'/(a)\1/v;',
            r'/\k<missing>/;',
            r'/(a)\k<missing>/;',
            r'/a{}/;',
            r'/a{,3}/;',
            r'/a{/;',
            r'/a\u007b1,2}+/;',
            r'/a*{x}/;',
            r'/a+?{x}/;',
            r'/a*{/;',
            r'/a*{}/;',
            r'/a*{,3}/;',
            r'/\p{ASCII/;',
            r'/\p{Definitely_Not_A_Property}/;',
            r'/\P{RGI_Emoji}/;',
            r'/\p{ASCII}(?:a)*/;',
            r'/\b{,3}/;',
            r'/\B{,3}/;',
            r'/\cA/;',
            r'/\cA{,3}/;',
            r'/\c/;',
            r'/\c*/;',
            r'/\q/;',
            r'/\q{ab}/;',
            r'/\u{1/;',
            r'/\u{10400}/;',
            r'/\u{110000}/;',
            r'/[]/;',
            r'/[^]/;',
            r'/[^]*/;',
            r'/[^]{,3}/;',
            r'/[\q{ab}]/;',
            r'/[\q{ab}]+/;',
            r'/[\cA]/;',
            r'/[\d-a]/;',
            r'/[a-\d]/;',
            r'/[\d-\w]/;',
            r'/[z-\d]/;',
            r'/[\d-z]/;',
            r'/[]/u;',
            r'/[^]/u;',
            r'/[\cA]/u;',
            r'/[\-]/u;',
            r'/[z-\u{10000}]/u;',
            r'/[z-\u{10000}]/v;',
            r'/[\u{10000}-\u{10001}]/u;',
            r'/[\u{10000}-\u{10001}]/v;',
            r'/[a--b]/v;',
            r'/[a&&b]/v;',
            r'/[a-b]/v;',
            r'/[[a--b]&&c]/v;',
            r'/[^]/v;',
            r'/[a&&\&]/v;',
            r'/[a&&[&]]/v;',
            r'/[\(\)\{\}\|\/]/v;',
            r'/[^\q{a}]/v;',
            r'/[^\q{\x61}]/v;',
            r'/[^\p{RGI_Emoji}&&a]/v;',
            r'/[\q{\}}]/v;',
            r'/[\q{ab|cd}]/v;',
            r'/[[a]&&\q{ab}]/v;',
            r'/[\p{Basic_Emoji}]/v;',
            r'/[\cA]/v;',
            r'/[\cA-B]/v;',
            r'/a\u{7b}/v;',
            r'/a\u007b/v;',
            r'/\u{28}/v;',
            r'/a\u{7b}/u;',
            r'/a\u007b/u;',
            r'/\u{28}/u;',
            r'/\p{ASCII}{2,3}/v;',
            r'/\p{ASCII}/v;',
            r'/\p{ASCII}/u;',
            r'/\p{ASCII}(?=a)/u;',
            r'/\p{ASCII}(?=a)/v;',
            r'/\p{ASCII}(?:a)*/u;',
            r'/[\b]*/u;',
            r'/[\b]*/v;',
            r'/\p{ASCII}\cA/v;',
            r'/\p{General_Category=Uppercase_Letter}/v;',
            r'/\p{Script=Greek}/v;',
            r'/\p{Script=Garay}/v;',
            r'/\p{Script=Todr}/v;',
            r'/\p{Script=Cuneiform}/v;',
            r'/\p{Script=Hira}/v;',
            r'/\p{Script=Kana}/v;',
            r'/\p{Script=Zzzz}/v;',
            r'/\p{RGI_Emoji}/v;',
        ]
        for src in modifier_cases:
            with self.subTest(src=src):
                parse(src)

        invalid_cases = [
            r'/(?<x>a)(?<x>b)/;',
            r'/(?<\u0061>a)(?<a>b)/;',
            r'/(?<x>a|(?<x>b))/;',
            r'/(?<\q>a)/;',
            r'/(?<\u00G0>a)/;',
            r'/(?<\u005c>a)/u;',
            r'/(?<\u005c>a)/v;',
            r'/(?<\u{1D7CE}>a)/u;',
            r'/(?<\u200c>a)/u;',
            r'/(?<\uD801>x)/u;',
            r'/(?<\uDC00>x)/u;',
            r'/(?<a\uD801>x)/u;',
            r'/(?<x>a)\k<missing>/;',
            r'/(?<x>a)[\k<x>]/u;',
            r'/(?ii:a)/;',
            r'/(?i-i:a)/;',
            r'/(?x:a)/;',
            r'/(?<x>a)\a/u;',
            r'/(?<x>a)\00/u;',
            r'/(a)\2/u;',
            r'/\3(a)(b)/u;',
            r'/\10(a)(b)/u;',
            r'/a\a/u;',
            r'/a\00/u;',
            r'/\x6\u0061/u;',
            r'/\x6\u{61}/u;',
            r'/\p{RGI_Emoji}/u;',
            r'/[\p{Basic_Emoji}]/u;',
            r'/[\p{ASCII}-a]/u;',
            r'/[a-\p{ASCII}]/u;',
            r'/[\u{10000}-a]/u;',
            r'/[\u{10000}-a]/v;',
            r'/[\u{10001}-\u{10000}]/u;',
            r'/[\u{10001}-\u{10000}]/v;',
            r'/\p{ASCII}(?=a)*/u;',
            r'/\p{ASCII}(?=a)+/u;',
            r'/\p{ASCII}(?=a)?/u;',
            r'/\p{ASCII}(?=a){1}/u;',
            r'/\p{ASCII}(?!a)*/u;',
            r'/\p{ASCII}(?<=a)*/u;',
            r'/\p{ASCII}(?<!a)*/u;',
            r'/(?=a)*/u;',
            r'/(?=a)*/v;',
            r'/\p{ASCII}(?=a)*/v;',
            r'/[a&&b](?=a)*/v;',
            r'/a++/;',
            r'/a{1,2}+/;',
            r'/\D++/;',
            r'/[\b]*+a/;',
            r'/a*{1}/;',
            r'/a+?{1}/;',
            r'/\p{ASCII}(?<=a)*/;',
            r'/\b{2,1}/;',
            r'/\B{2,1}/;',
            r'/\cA{2,1}/;',
            r'/\c*{2,1}/;',
            r'/(?<=a){1}/;',
            r'/[^]{2,1}/;',
            r'/[\q{ab}]+{2,1}/;',
            r'/[\p{ASCII}]*{2,1}/;',
            r'/[\a-\b]/;',
            r'/[\cZ-\cA]/;',
            r'/[\q-a]/;',
            r'/a++/u;',
            r'/a{1,2}+/u;',
            r'/\p{ASCII}++/v;',
            r'/[\b]*+a/u;',
            r'/a+??/u;',
            r'/a{1}?+/u;',
            r'/\p{ASCII}\a/v;',
            r'/[\a]/v;',
            r'/a/gg;',
            r'/a/z;',
            r'/a/uv;',
            r'/(/v;',
            r'/]/v;',
            r'/}/v;',
            r'/]/u;',
            r'/}/u;',
            r'/[z-a]/v;',
            r'/[a--]/v;',
            r'/[a&&]/v;',
            r'/[a--b&&c]/v;',
            r'/[a&&&]/v;',
            r'/[[a]&&b]/u;',
            r'/[|]/v;',
            r'/[(){}]/v;',
            r'/[a||b]/v;',
            r'/[!!]/v;',
            r'/[a-]/v;',
            r'/[-]/v;',
            r'/[[a]\//v;',
            r'/[^\p{RGI_Emoji}]/v;',
            r'/[^\q{ab}]/v;',
            r'/[\q{\d}]/v;',
            r'/[\q{\a}]/v;',
            r'/\p{ASCII}{}/v;',
            r'/\p{ASCII}{/v;',
            r'/\p{ASCII}{3,2}/v;',
            r'/a{}/u;',
            r'/a{,3}/u;',
            r'/a{/u;',
            r'/{/u;',
            r'/\p{Definitely_Not_A_Property}/v;',
            r'/\p{Script=Definitely_Not_A_Property}/v;',
            r'/\p{Script=Hrkt}/v;',
            r'/\p{Script_Extensions=Hrkt}/v;',
            r'/\p{Script=Katakana_Or_Hiragana}/v;',
            r'/\p{Script_Extensions=Katakana_Or_Hiragana}/v;',
            r'/\p{ASCII/v;',
            r'/\P{RGI_Emoji}/v;',
            r'/[\q{ab]/v;',
        ]
        for src in invalid_cases:
            with self.subTest(src=src):
                with self.assertRaises(Error):
                    parse(src)

    def find_executable(self, name):
        for path in os.environ.get('PATH', '').split(os.pathsep):
            candidate = os.path.join(path, name)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        return None

    def node_regexp_accepts(self, node, literal):
        script = (
            "const literal = process.argv[1];"
            "const last = literal.lastIndexOf('/');"
            "if (literal[0] !== '/' || last <= 0) process.exit(2);"
            "try { new RegExp(literal.slice(1, last), literal.slice(last + 1)); process.exit(0); }"
            "catch (e) { process.exit(1); }"
        )
        with open(os.devnull, 'wb') as devnull:
            status = subprocess.call([node, '-e', script, literal], stdout=devnull, stderr=devnull)
        return status == 0

    def test_ecma2025_regexp_node_differential_cases(self):
        node = self.find_executable('node')
        if not node:
            self.skipTest('node is not available')

        if not self.node_regexp_accepts(node, r'/./v'):
            self.skipTest('node does not support the v regexp flag')

        cases = [
            r'/(?<year>\d{4})-\k<year>/',
            r'/(?i-:abc)/',
            r'/[a--b]/v',
            r'/[a&&b]/v',
            r'/[^]/v',
            r'/[^\q{\x61}]/v',
            r'/[\q{\}}]/v',
            r'/[[a]&&\q{ab}]/v',
            r'/\p{ASCII}{2,3}/v',
            r'/\p{ASCII}\cA/v',
            r'/(?<\u{10400}>a)\k<\u{10400}>/u',
            r'/(?<\u{10400}>a)\k<\u{10400}>/v',
            r'/(?<a\u{10400}>x)/u',
            r'/(?<a\u{10400}>x)/v',
            r'/(?<\uD801\uDC00>x)/u',
            r'/(?<\uD801\uDC00>x)/v',
            r'/(?<a\uD801\uDC00>x)/u',
            r'/(?<\u{10400}>x)/',
            r'/(?<a\u{10400}>x)/',
            r'/(?<a\u{1D7CE}>a)/u',
            r'/(?<a\u200c>a)/u',
            r'/(?<=\d+)/u',
            r'/(?<=\d+)/v',
            r'/(?<=\p{RGI_Emoji}*)/v',
            r'/\1(a)/u',
            r'/\1(a)/v',
            r'/\2(a)(b)/u',
            r'/\10(a)(b)(c)(d)(e)(f)(g)(h)(i)(j)/u',
            r'/(a)\1/u',
            r'/(a)\1/v',
            r'/\k<missing>/',
            r'/(a)\k<missing>/',
            r'/a{}/',
            r'/a{,3}/',
            r'/a{/',
            r'/a\u007b1,2}+/',
            r'/a*{x}/',
            r'/a+?{x}/',
            r'/a*{/',
            r'/a*{}/',
            r'/a*{,3}/',
            r'/\p{ASCII/',
            r'/\p{Definitely_Not_A_Property}/',
            r'/\P{RGI_Emoji}/',
            r'/\p{ASCII}(?:a)*/',
            r'/\b{,3}/',
            r'/\B{,3}/',
            r'/\cA/',
            r'/\cA{,3}/',
            r'/\c/',
            r'/\c*/',
            r'/\q/',
            r'/\q{ab}/',
            r'/\u{1/',
            r'/\u{10400}/',
            r'/\u{110000}/',
            r'/[]/',
            r'/[^]/',
            r'/[^]*/',
            r'/[^]{,3}/',
            r'/[\q{ab}]/',
            r'/[\q{ab}]+/',
            r'/[\cA]/',
            r'/[\d-a]/',
            r'/[a-\d]/',
            r'/[\d-\w]/',
            r'/[z-\d]/',
            r'/[\d-z]/',
            r'/[]/u',
            r'/[^]/u',
            r'/\p{ASCII}(?=a)/u',
            r'/\p{ASCII}(?=a)/v',
            r'/\p{ASCII}(?:a)*/u',
            r'/[\b]*/u',
            r'/[\b]*/v',
            r'/[z-\u{10000}]/u',
            r'/[z-\u{10000}]/v',
            r'/[\u{10000}-\u{10001}]/u',
            r'/[\u{10000}-\u{10001}]/v',
            r'/\p{RGI_Emoji}/v',
            r'/[\p{Basic_Emoji}]/v',
            r'/[\cA]/v',
            r'/[\cA-B]/v',
            r'/a\u{7b}/v',
            r'/a\u007b/v',
            r'/\u{28}/v',
            r'/a\u{7b}/u',
            r'/a\u007b/u',
            r'/\u{28}/u',
            r'/(?<\q>a)/',
            r'/(?<\u005c>a)/u',
            r'/(?<\u005c>a)/v',
            r'/(?<\u{1D7CE}>a)/u',
            r'/(?<\u200c>a)/u',
            r'/(?<\uD801>x)/u',
            r'/(?<\uDC00>x)/u',
            r'/(?<a\uD801>x)/u',
            r'/(?<x>a)\k<missing>/',
            r'/(?<x>a)[\k<x>]/u',
            r'/(?<x>a)\a/u',
            r'/(?<x>a)\00/u',
            r'/(a)\2/u',
            r'/\3(a)(b)/u',
            r'/\10(a)(b)/u',
            r'/\x6\u0061/u',
            r'/\x6\u{61}/u',
            r'/(/v',
            r'/]/v',
            r'/}/v',
            r'/]/u',
            r'/}/u',
            r'/[z-a]/v',
            r'/[a--]/v',
            r'/[a&&]/v',
            r'/[a--b&&c]/v',
            r'/[a&&&]/v',
            r'/[[a]&&b]/u',
            r'/[\p{ASCII}-a]/u',
            r'/[a-\p{ASCII}]/u',
            r'/[\u{10000}-a]/u',
            r'/[\u{10000}-a]/v',
            r'/[\u{10001}-\u{10000}]/u',
            r'/[\u{10001}-\u{10000}]/v',
            r'/\p{ASCII}(?=a)*/u',
            r'/\p{ASCII}(?=a)+/u',
            r'/\p{ASCII}(?=a)?/u',
            r'/\p{ASCII}(?=a){1}/u',
            r'/\p{ASCII}(?!a)*/u',
            r'/\p{ASCII}(?<=a)*/u',
            r'/\p{ASCII}(?<!a)*/u',
            r'/(?=a)*/u',
            r'/(?=a)*/v',
            r'/\p{ASCII}(?=a)*/v',
            r'/[a&&b](?=a)*/v',
            r'/a++/',
            r'/a{1,2}+/',
            r'/\D++/',
            r'/[\b]*+a/',
            r'/a*{1}/',
            r'/a+?{1}/',
            r'/\p{ASCII}(?<=a)*/',
            r'/\b{2,1}/',
            r'/\B{2,1}/',
            r'/\cA{2,1}/',
            r'/\c*{2,1}/',
            r'/(?<=a){1}/',
            r'/[^]{2,1}/',
            r'/[\q{ab}]+{2,1}/',
            r'/[\p{ASCII}]*{2,1}/',
            r'/[\a-\b]/',
            r'/[\cZ-\cA]/',
            r'/[\q-a]/',
            r'/a++/u',
            r'/a{1,2}+/u',
            r'/\p{ASCII}++/v',
            r'/[\b]*+a/u',
            r'/a+??/u',
            r'/a{1}?+/u',
            r'/[|]/v',
            r'/[(){}]/v',
            r'/[a||b]/v',
            r'/[[a]\//v',
            r'/[^\p{RGI_Emoji}]/v',
            r'/[^\q{ab}]/v',
            r'/[\q{\d}]/v',
            r'/\p{ASCII}{}/v',
            r'/a{}/u',
            r'/a{,3}/u',
            r'/a{/u',
            r'/{/u',
            r'/\p{Definitely_Not_A_Property}/v',
            r'/\p{Script=Hrkt}/v',
            r'/\p{Script_Extensions=Hrkt}/v',
            r'/\p{Script=Katakana_Or_Hiragana}/v',
            r'/\p{Script_Extensions=Katakana_Or_Hiragana}/v',
            r'/\p{ASCII/v',
            r'/\P{RGI_Emoji}/v',
            r'/\p{RGI_Emoji}/u',
            r'/[\p{Basic_Emoji}]/u',
            r'/[\a]/v',
        ]
        for literal in cases:
            with self.subTest(literal=literal):
                node_ok = self.node_regexp_accepts(node, literal)
                try:
                    parse(literal + ';')
                    parser_ok = True
                except Error:
                    parser_ok = False
                self.assertEqual(node_ok, parser_ok)


# class TestThirdParty(unittest.TestCase):
#     pass


# for path in glob.glob(os.path.join(BASE_DIR, '3rdparty', '*.js')):
#     for test_name, test in test_factory(path):
#         setattr(TestThirdParty, 'test_%s' % test_name, test)


for fixture_path in glob.glob(os.path.join(BASE_DIR, 'fixtures', '*')):
    class_name = os.path.basename(fixture_path).replace('-', ' ').replace('.', ' ')
    class_name = 'Test%s' % ''.join((n.capitalize() if n.islower() else n) for n in class_name.split())
    Test = type(class_name, (unittest.TestCase,), {'maxDiff': None})  # {'maxDiff': None}
    globals()[class_name] = Test
    for path in glob.glob(os.path.join(fixture_path, '*')):
        if os.path.isdir(path) or fnmatch.fnmatch(path, '*.js'):
            for test_name, test in test_factory(path):
                if (class_name, test_name) in EXPECTED_FAULRES:
                    test = unittest.expectedFailure(test)
                setattr(Test, 'test_%s' % test_name, test)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
