**esprima2** is a javascript parser written in python. It works for ECMAScript 2024 and has ~1500 unit tests.

#### Credits
1. [Ariya Hidayat](https://x.com/ariyahidayat) created the original [esprima]((https://github.com/jquery/esprima) library.
2. [Kronuz](https://github.com/Kronuz/esprima-python) created a python port as [esprima-python](https://github.com/Kronuz/esprima-python), line-by-line - faithfully.
3. `esprima` library hasn't been updated since ECMAScript 2019 and `esprima-python` since ECMAScript 2017.
4. With `esprima2`, I added the missing syntax support and now we can parse modern javascript.

## Features
-  Full support for [ECMAScript 2024](https://www.ecma-international.org/publications-and-standards/standards/ecma-262/>)
-  Sensible [syntax tree format](https://github.com/estree/estree/blob/master/es5.md) as tandardized by [ESTree project](https://github.com/estree/estree)
-  Experimental support for [JSX](https://facebook.github.io/jsx/), a syntax extension for [React](https://facebook.github.io/react/)
-  Optional tracking of syntax node location (index-based and line-column)
-  [Heavily tested](https://esprima.org/test/ci.html) (~1500 [unit tests](https://github.com/s0md3v/esprima/tree/master/test/fixtures))

## Installation

```shell
pip install esprima2
```

## Usage

Esprima can be used to perform [lexical analysis](https://en.wikipedia.org/wiki/Lexical_analysis>)
(tokenization) or [syntactic analysis](https://en.wikipedia.org/wiki/Parsing>) (parsing) a JavaScript program.

A simple example:

```javascript

    >>> import esprima
    >>> program = 'const answer = 42'

    >>> esprima.tokenize(program)
    [{
        type: "Keyword",
        value: "const"
    }, {
        type: "Identifier",
        value: "answer"
    }, {
        type: "Punctuator",
        value: "="
    }, {
        type: "Numeric",
        value: "42"
    }]

    >>> esprima.parseScript(program)
    {
        body: [
            {
                kind: "const",
                declarations: [
                    {
                        init: {
                            raw: "42",
                            type: "Literal",
                            value: 42
                        },
                        type: "VariableDeclarator",
                        id: {
                            type: "Identifier",
                            name: "answer"
                        }
                    }
                ],
                type: "VariableDeclaration"
            }
        ],
        type: "Program",
        sourceType: "script"
    }
```

More (and original) documentation is available here: [https://esprima.org](https://esprima.org/)
