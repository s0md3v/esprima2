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

from __future__ import absolute_import

import os
import re
import json
import glob
import fnmatch
import unittest

from esprima import parse, tokenize, Error, toDict
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
