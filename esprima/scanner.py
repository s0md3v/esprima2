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


import re
import unicodedata
import warnings

from .objects import Object
from .character import Character, HEX_CONV
from .messages import Messages
from .token import Token

warnings.simplefilter(action='ignore', category=FutureWarning)

def hexDigitValue(ch):
    return HEX_CONV[ch]

_zeroDigitCode = ord("0")

def octalDigitValue(ch):
    return ord(ch) - _zeroDigitCode


class RegExp(Object):
    def __init__(self, pattern=None, flags=None):
        self.pattern = pattern
        self.flags = flags


class Position(Object):
    def __init__(self, line=None, column=None, offset=None):
        self.line = line
        self.column = column
        self.offset = offset


class SourceLocation(Object):
    def __init__(self, start=None, end=None, source=None):
        self.start = start
        self.end = end
        self.source = source


class Comment(Object):
    def __init__(self, multiLine=None, slice=None, range=None, loc=None):
        self.multiLine = multiLine
        self.slice = slice
        self.range = range
        self.loc = loc


class RawToken(Object):
    def __init__(self, type=None, value=None, pattern=None, flags=None, regex=None, octal=None, cooked=None, head=None, tail=None, lineNumber=None, lineStart=None, start=None, end=None, raw=None):
        self.type = type
        self.value = value
        self.pattern = pattern
        self.flags = flags
        self.regex = regex
        self.octal = octal
        self.cooked = cooked
        self.head = head
        self.tail = tail
        self.lineNumber = lineNumber
        self.lineStart = lineStart
        self.start = start
        self.end = end
        self.raw = raw


class ScannerState(Object):
    def __init__(self, index=None, lineNumber=None, lineStart=None):
        self.index = index
        self.lineNumber = lineNumber
        self.lineStart = lineStart


class Octal(object):
    def __init__(self, octal, code):
        self.octal = octal
        self.code = code


REGEXP_UNICODE_PROPERTY_NAMES = set((
    'General_Category', 'gc',
    'Script', 'sc',
    'Script_Extensions', 'scx',
))

REGEXP_GENERAL_CATEGORY_VALUES = set((
    'C', 'Other', 'Cc', 'Control', 'cntrl', 'Cf', 'Format', 'Cn', 'Unassigned',
    'Co', 'Private_Use', 'Cs', 'Surrogate',
    'L', 'Letter', 'LC', 'Cased_Letter', 'Ll', 'Lowercase_Letter',
    'Lm', 'Modifier_Letter', 'Lo', 'Other_Letter', 'Lt', 'Titlecase_Letter',
    'Lu', 'Uppercase_Letter',
    'M', 'Mark', 'Combining_Mark', 'Mc', 'Spacing_Mark',
    'Me', 'Enclosing_Mark', 'Mn', 'Nonspacing_Mark',
    'N', 'Number', 'Nd', 'Decimal_Number', 'digit', 'Nl', 'Letter_Number',
    'No', 'Other_Number',
    'P', 'Punctuation', 'punct', 'Pc', 'Connector_Punctuation',
    'Pd', 'Dash_Punctuation', 'Pe', 'Close_Punctuation',
    'Pf', 'Final_Punctuation', 'Pi', 'Initial_Punctuation',
    'Po', 'Other_Punctuation', 'Ps', 'Open_Punctuation',
    'S', 'Symbol', 'Sc', 'Currency_Symbol', 'Sk', 'Modifier_Symbol',
    'Sm', 'Math_Symbol', 'So', 'Other_Symbol',
    'Z', 'Separator', 'Zl', 'Line_Separator', 'Zp', 'Paragraph_Separator',
    'Zs', 'Space_Separator',
))

REGEXP_SCRIPT_VALUES = set((
    'Adlam', 'Adlm', 'Ahom', 'Anatolian_Hieroglyphs', 'Hluw', 'Arabic', 'Arab',
    'Armenian', 'Armn', 'Avestan', 'Avst', 'Balinese', 'Bali', 'Bamum', 'Bamu',
    'Bassa_Vah', 'Bass', 'Batak', 'Batk', 'Bengali', 'Beng', 'Bhaiksuki',
    'Bhks', 'Bopomofo', 'Bopo', 'Brahmi', 'Brah', 'Braille', 'Brai',
    'Buginese', 'Bugi', 'Buhid', 'Buhd', 'Canadian_Aboriginal', 'Cans',
    'Carian', 'Cari', 'Caucasian_Albanian', 'Aghb', 'Chakma', 'Cakm', 'Cham',
    'Cherokee', 'Cher', 'Chorasmian', 'Chrs', 'Common', 'Zyyy', 'Coptic',
    'Copt', 'Qaac', 'Cuneiform', 'Xsux', 'Cypriot', 'Cprt', 'Cypro_Minoan', 'Cpmn', 'Cyrillic',
    'Cyrl', 'Deseret', 'Dsrt', 'Devanagari', 'Deva', 'Dives_Akuru', 'Diak',
    'Dogra', 'Dogr', 'Duployan', 'Dupl', 'Egyptian_Hieroglyphs', 'Egyp',
    'Elbasan', 'Elba', 'Elymaic', 'Elym', 'Ethiopic', 'Ethi', 'Garay', 'Gara',
    'Georgian', 'Geor', 'Glagolitic', 'Glag', 'Gothic', 'Goth',
    'Grantha', 'Gran', 'Greek', 'Grek', 'Gujarati', 'Gujr', 'Gunjala_Gondi',
    'Gong', 'Gurmukhi', 'Guru', 'Gurung_Khema', 'Gukh',
    'Han', 'Hani', 'Hangul', 'Hang', 'Hanifi_Rohingya', 'Rohg', 'Hanunoo',
    'Hano', 'Hatran', 'Hatr', 'Hebrew', 'Hebr', 'Hiragana', 'Hira',
    'Imperial_Aramaic', 'Armi', 'Inherited', 'Zinh', 'Qaai',
    'Inscriptional_Pahlavi', 'Phli', 'Inscriptional_Parthian', 'Prti',
    'Javanese', 'Java', 'Kaithi', 'Kthi', 'Kannada', 'Knda', 'Katakana',
    'Kana', 'Kawi', 'Kayah_Li', 'Kali', 'Kharoshthi', 'Khar',
    'Khitan_Small_Script', 'Kits', 'Kirat_Rai', 'Krai', 'Khmer', 'Khmr', 'Khojki', 'Khoj',
    'Khudawadi', 'Sind', 'Lao', 'Laoo', 'Latin', 'Latn', 'Lepcha', 'Lepc',
    'Limbu', 'Limb', 'Linear_A', 'Lina', 'Linear_B', 'Linb', 'Lisu',
    'Lycian', 'Lyci', 'Lydian', 'Lydi', 'Mahajani', 'Mahj', 'Makasar', 'Maka',
    'Malayalam', 'Mlym', 'Mandaic', 'Mand', 'Manichaean', 'Mani', 'Marchen',
    'Marc', 'Masaram_Gondi', 'Gonm', 'Medefaidrin', 'Medf', 'Meetei_Mayek',
    'Mtei', 'Mende_Kikakui', 'Mend', 'Meroitic_Cursive', 'Merc',
    'Meroitic_Hieroglyphs', 'Mero', 'Miao', 'Plrd', 'Modi', 'Mongolian',
    'Mong', 'Mro', 'Mroo', 'Multani', 'Mult', 'Myanmar', 'Mymr', 'Nabataean',
    'Nbat', 'Nag_Mundari', 'Nagm', 'Nandinagari', 'Nand', 'New_Tai_Lue',
    'Talu', 'Newa', 'Nko', 'Nkoo', 'Nushu', 'Nshu', 'Nyiakeng_Puachue_Hmong',
    'Hmnp', 'Ogham', 'Ogam', 'Ol_Chiki', 'Olck', 'Ol_Onal', 'Onao',
    'Old_Hungarian', 'Hung',
    'Old_Italic', 'Ital', 'Old_North_Arabian', 'Narb', 'Old_Permic', 'Perm',
    'Old_Persian', 'Xpeo', 'Old_Sogdian', 'Sogo', 'Old_South_Arabian', 'Sarb',
    'Old_Turkic', 'Orkh', 'Old_Uyghur', 'Ougr', 'Oriya', 'Orya', 'Osage',
    'Osge', 'Osmanya', 'Osma', 'Pahawh_Hmong', 'Hmng', 'Palmyrene', 'Palm',
    'Pau_Cin_Hau', 'Pauc', 'Phags_Pa', 'Phag', 'Phoenician', 'Phnx',
    'Psalter_Pahlavi', 'Phlp', 'Rejang', 'Rjng', 'Runic', 'Runr',
    'Samaritan', 'Samr', 'Saurashtra', 'Saur', 'Sharada', 'Shrd', 'Shavian',
    'Shaw', 'Siddham', 'Sidd', 'SignWriting', 'Sgnw', 'Sinhala', 'Sinh',
    'Sogdian', 'Sogd', 'Sora_Sompeng', 'Sora', 'Soyombo', 'Soyo', 'Sundanese',
    'Sund', 'Sunuwar', 'Sunu', 'Syloti_Nagri', 'Sylo', 'Syriac', 'Syrc', 'Tagalog', 'Tglg',
    'Tagbanwa', 'Tagb', 'Tai_Le', 'Tale', 'Tai_Tham', 'Lana', 'Tai_Viet',
    'Tavt', 'Takri', 'Takr', 'Tamil', 'Taml', 'Tangsa', 'Tnsa', 'Tangut',
    'Tang', 'Telugu', 'Telu', 'Thaana', 'Thaa', 'Thai', 'Tibetan', 'Tibt',
    'Tifinagh', 'Tfng', 'Tirhuta', 'Tirh', 'Todhri', 'Todr', 'Toto',
    'Tulu_Tigalari', 'Tutg', 'Ugaritic', 'Ugar', 'Vai', 'Vaii',
    'Vithkuqi', 'Vith', 'Wancho', 'Wcho', 'Warang_Citi', 'Wara',
    'Yezidi', 'Yezi', 'Yi', 'Yiii', 'Zanabazar_Square', 'Zanb', 'Unknown', 'Zzzz',
))

REGEXP_BINARY_UNICODE_PROPERTIES = set((
    'ASCII', 'Any', 'Assigned',
    'ASCII_Hex_Digit', 'AHex', 'Alphabetic', 'Alpha',
    'Bidi_Control', 'Bidi_C', 'Bidi_Mirrored', 'Bidi_M',
    'Case_Ignorable', 'CI', 'Cased',
    'Changes_When_Casefolded', 'CWCF', 'Changes_When_Casemapped', 'CWCM',
    'Changes_When_Lowercased', 'CWL', 'Changes_When_NFKC_Casefolded', 'CWKCF',
    'Changes_When_Titlecased', 'CWT', 'Changes_When_Uppercased', 'CWU',
    'Dash', 'Default_Ignorable_Code_Point', 'DI',
    'Deprecated', 'Dep', 'Diacritic', 'Dia',
    'Emoji', 'Emoji_Component', 'EComp', 'Emoji_Modifier', 'EMod',
    'Emoji_Modifier_Base', 'EBase', 'Emoji_Presentation', 'EPres',
    'Extended_Pictographic', 'ExtPict', 'Extender', 'Ext',
    'Grapheme_Base', 'Gr_Base', 'Grapheme_Extend', 'Gr_Ext',
    'Hex_Digit', 'Hex', 'IDS_Binary_Operator', 'IDSB',
    'IDS_Trinary_Operator', 'IDST', 'ID_Continue', 'IDC', 'ID_Start', 'IDS',
    'Ideographic', 'Ideo', 'Join_Control', 'Join_C',
    'Logical_Order_Exception', 'LOE', 'Lowercase', 'Lower',
    'Math', 'Noncharacter_Code_Point', 'NChar',
    'Pattern_Syntax', 'Pat_Syn', 'Pattern_White_Space', 'Pat_WS',
    'Quotation_Mark', 'QMark', 'Radical', 'Regional_Indicator', 'RI',
    'Sentence_Terminal', 'STerm', 'Soft_Dotted', 'SD',
    'Terminal_Punctuation', 'Term', 'Unified_Ideograph', 'UIdeo',
    'Uppercase', 'Upper', 'Variation_Selector', 'VS',
    'White_Space', 'space', 'XID_Continue', 'XIDC', 'XID_Start', 'XIDS',
))

REGEXP_BINARY_PROPERTIES_OF_STRINGS = set((
    'Basic_Emoji',
    'Emoji_Keycap_Sequence',
    'RGI_Emoji',
    'RGI_Emoji_Flag_Sequence',
    'RGI_Emoji_Modifier_Sequence',
    'RGI_Emoji_Tag_Sequence',
    'RGI_Emoji_ZWJ_Sequence',
))

REGEXP_CLASS_SET_SYNTAX_CHARACTERS = set('()[]{}/-\\|')

REGEXP_CLASS_SET_RESERVED_DOUBLE_PUNCTUATORS = set((
    '&&', '!!', '##', '$$', '%%', '**', '++', ',,', '..', '::', ';;',
    '<<', '==', '>>', '??', '@@', '^^', '``', '~~',
))

REGEXP_IDENTITY_ESCAPE_CHARACTERS = set('^$\\.*+?()[]{}|/')


class Scanner(object):
    def __init__(self, code, handler):
        self.source = str(code) + '\x00'
        self.errorHandler = handler
        self.trackComment = False
        self.isModule = False

        self.length = len(code)
        self.index = 0
        self.lineNumber = 1 if self.length > 0 else 0
        self.lineStart = 0
        self.curlyStack = []

    def saveState(self):
        return ScannerState(
            index=self.index,
            lineNumber=self.lineNumber,
            lineStart=self.lineStart
        )

    def restoreState(self, state):
        self.index = state.index
        self.lineNumber = state.lineNumber
        self.lineStart = state.lineStart

    def eof(self):
        return self.index >= self.length

    def throwUnexpectedToken(self, message=Messages.UnexpectedTokenIllegal):
        return self.errorHandler.throwError(self.index, self.lineNumber,
            self.index - self.lineStart + 1, message)

    def tolerateUnexpectedToken(self, message=Messages.UnexpectedTokenIllegal):
        self.errorHandler.tolerateError(self.index, self.lineNumber,
            self.index - self.lineStart + 1, message)

    # https://tc39.github.io/ecma262/#sec-comments

    def skipSingleLineComment(self, offset):
        comments = []

        if self.trackComment:
            start = self.index - offset
            loc = SourceLocation(
                start=Position(
                    line=self.lineNumber,
                    column=self.index - self.lineStart - offset
                ),
                end=Position()
            )

        while not self.eof():
            ch = self.source[self.index]
            self.index += 1
            if Character.isLineTerminator(ch):
                if self.trackComment:
                    loc.end = Position(
                        line=self.lineNumber,
                        column=self.index - self.lineStart - 1
                    )
                    entry = Comment(
                        multiLine=False,
                        slice=[start + offset, self.index - 1],
                        range=[start, self.index - 1],
                        loc=loc
                    )
                    comments.append(entry)

                if ch == '\r' and self.source[self.index] == '\n':
                    self.index += 1

                self.lineNumber += 1
                self.lineStart = self.index
                return comments

        if self.trackComment:
            loc.end = Position(
                line=self.lineNumber,
                column=self.index - self.lineStart
            )
            entry = Comment(
                multiLine=False,
                slice=[start + offset, self.index],
                range=[start, self.index],
                loc=loc
            )
            comments.append(entry)

        return comments

    def skipMultiLineComment(self):
        comments = []

        if self.trackComment:
            comments = []
            start = self.index - 2
            loc = SourceLocation(
                start=Position(
                    line=self.lineNumber,
                    column=self.index - self.lineStart - 2
                ),
                end=Position()
            )

        while not self.eof():
            ch = self.source[self.index]
            if Character.isLineTerminator(ch):
                if ch == '\r' and self.source[self.index + 1] == '\n':
                    self.index += 1

                self.lineNumber += 1
                self.index += 1
                self.lineStart = self.index
            elif ch == '*':
                # Block comment ends with '*/'.
                if self.source[self.index + 1] == '/':
                    self.index += 2
                    if self.trackComment:
                        loc.end = Position(
                            line=self.lineNumber,
                            column=self.index - self.lineStart
                        )
                        entry = Comment(
                            multiLine=True,
                            slice=[start + 2, self.index - 2],
                            range=[start, self.index],
                            loc=loc
                        )
                        comments.append(entry)

                    return comments

                self.index += 1
            else:
                self.index += 1

        # Ran off the end of the file - the whole thing is a comment
        if self.trackComment:
            loc.end = Position(
                line=self.lineNumber,
                column=self.index - self.lineStart
            )
            entry = Comment(
                multiLine=True,
                slice=[start + 2, self.index],
                range=[start, self.index],
                loc=loc
            )
            comments.append(entry)

        self.tolerateUnexpectedToken()
        return comments

    def scanComments(self):
        comments = []

        start = self.index == 0
        while not self.eof():
            ch = self.source[self.index]

            if Character.isWhiteSpace(ch):
                self.index += 1
            elif Character.isLineTerminator(ch):
                self.index += 1
                if ch == '\r' and self.source[self.index] == '\n':
                    self.index += 1

                self.lineNumber += 1
                self.lineStart = self.index
                start = True
            elif ch == '/':  # U+002F is '/'
                ch = self.source[self.index + 1]
                if ch == '/':
                    self.index += 2
                    comment = self.skipSingleLineComment(2)
                    if self.trackComment:
                        comments.extend(comment)

                    start = True
                elif ch == '*':  # U+002A is '*'
                    self.index += 2
                    comment = self.skipMultiLineComment()
                    if self.trackComment:
                        comments.extend(comment)

                else:
                    break

            elif start and ch == '-':  # U+002D is '-'
                # U+003E is '>'
                if self.source[self.index + 1:self.index + 3] == '->':
                    # '-->' is a single-line comment
                    self.index += 3
                    comment = self.skipSingleLineComment(3)
                    if self.trackComment:
                        comments.extend(comment)

                else:
                    break

            elif ch == '<' and not self.isModule:  # U+003C is '<'
                if self.source[self.index + 1:self.index + 4] == '!--':
                    self.index += 4  # `<!--`
                    comment = self.skipSingleLineComment(4)
                    if self.trackComment:
                        comments.extend(comment)

                else:
                    break

            else:
                break

        return comments

    # https://tc39.github.io/ecma262/#sec-future-reserved-words

    def isFutureReservedWord(self, id):
        return id in self.isFutureReservedWord.set
    isFutureReservedWord.set = set((
        'enum',
        'export',
        'import',
        'super',
    ))

    def isStrictModeReservedWord(self, id):
        return id in self.isStrictModeReservedWord.set
    isStrictModeReservedWord.set = set((
        'implements',
        'interface',
        'package',
        'private',
        'protected',
        'public',
        'static',
        'yield',
        'let',
    ))

    def isRestrictedWord(self, id):
        return id in self.isRestrictedWord.set
    isRestrictedWord.set = set((
        'eval', 'arguments',
    ))

    # https://tc39.github.io/ecma262/#sec-keywords

    def isKeyword(self, id):
        return id in self.isKeyword.set
    isKeyword.set = set((
        'if', 'in', 'do',

        'var', 'for', 'new',
        'try', 'let',

        'this', 'else', 'case',
        'void', 'with', 'enum',

        'while', 'break', 'catch',
        'throw', 'const', 'yield',
        'class', 'super',

        'return', 'typeof', 'delete',
        'switch', 'export', 'import',

        'default', 'finally', 'extends',

        'function', 'continue', 'debugger',

        'instanceof',
    ))

    def codePointAt(self, i):
        return ord(self.source[i])

    def scanHexEscape(self, prefix):
        length = 4 if prefix == 'u' else 2
        code = 0

        for i in range(length):
            if not self.eof() and Character.isHexDigit(self.source[self.index]):
                ch = self.source[self.index]
                self.index += 1
                code = code * 16 + hexDigitValue(ch)
            else:
                return None

        return chr(code)

    def scanUnicodeCodePointEscape(self):
        ch = self.source[self.index]
        code = 0

        # At least, one hex digit is required.
        if ch == '}':
            self.throwUnexpectedToken()

        while not self.eof():
            ch = self.source[self.index]
            self.index += 1
            if not Character.isHexDigit(ch):
                break

            code = code * 16 + hexDigitValue(ch)

        if code > 0x10FFFF or ch != '}':
            self.throwUnexpectedToken()

        return Character.fromCodePoint(code)

    def getIdentifier(self):
        start = self.index
        self.index += 1
        while not self.eof():
            ch = self.source[self.index]
            if ch == '\\':
                # Blackslash (U+005C) marks Unicode escape sequence.
                self.index = start
                return self.getComplexIdentifier()
            else:
                cp = ord(ch)
                if cp >= 0xD800 and cp < 0xDFFF:
                    # Need to handle surrogate pairs.
                    self.index = start
                    return self.getComplexIdentifier()

            if Character.isIdentifierPart(ch):
                self.index += 1
            else:
                break

        return self.source[start:self.index]

    def getComplexIdentifier(self):
        cp = self.codePointAt(self.index)
        id = Character.fromCodePoint(cp)
        self.index += len(id)

        # '\u' (U+005C, U+0075) denotes an escaped character.
        if cp == 0x5C:
            if self.source[self.index] != 'u':
                self.throwUnexpectedToken()

            self.index += 1
            if self.source[self.index] == '{':
                self.index += 1
                ch = self.scanUnicodeCodePointEscape()
            else:
                ch = self.scanHexEscape('u')
                if not ch or ch == '\\' or not Character.isIdentifierStart(ch[0]):
                    self.throwUnexpectedToken()

            id = ch

        while not self.eof():
            cp = self.codePointAt(self.index)
            ch = Character.fromCodePoint(cp)
            if not Character.isIdentifierPart(ch):
                break

            id += ch
            self.index += len(ch)

            # '\u' (U+005C, U+0075) denotes an escaped character.
            if cp == 0x5C:
                id = id[:-1]
                if self.source[self.index] != 'u':
                    self.throwUnexpectedToken()

                self.index += 1
                if self.source[self.index] == '{':
                    self.index += 1
                    ch = self.scanUnicodeCodePointEscape()
                else:
                    ch = self.scanHexEscape('u')
                    if not ch or ch == '\\' or not Character.isIdentifierPart(ch[0]):
                        self.throwUnexpectedToken()

                id += ch

        return id

    def octalToDecimal(self, ch):
        # \0 is not octal escape sequence
        octal = ch != '0'
        code = octalDigitValue(ch)

        if not self.eof() and Character.isOctalDigit(self.source[self.index]):
            octal = True
            code = code * 8 + octalDigitValue(self.source[self.index])
            self.index += 1

            # 3 digits are only allowed when string starts
            # with 0, 1, 2, 3
            if ch in '0123' and not self.eof() and Character.isOctalDigit(self.source[self.index]):
                code = code * 8 + octalDigitValue(self.source[self.index])
                self.index += 1

        return Octal(octal, code)

    # https://tc39.github.io/ecma262/#sec-names-and-keywords

    def scanIdentifier(self):
        start = self.index

        # Backslash (U+005C) starts an escaped character.
        id = self.getComplexIdentifier() if self.source[start] == '\\' else self.getIdentifier()

        # There is no keyword or literal with only one character.
        # Thus, it must be an identifier.
        if len(id) == 1:
            type = Token.Identifier
        elif self.isKeyword(id):
            type = Token.Keyword
        elif id == 'null':
            type = Token.NullLiteral
        elif id == 'true' or id == 'false':
            type = Token.BooleanLiteral
        else:
            type = Token.Identifier

        if type is not Token.Identifier and start + len(id) != self.index:
            restore = self.index
            self.index = start
            self.tolerateUnexpectedToken(Messages.InvalidEscapedReservedWord)
            self.index = restore

        return RawToken(
            type=type,
            value=id,
            lineNumber=self.lineNumber,
            lineStart=self.lineStart,
            start=start,
            end=self.index
        )

    def scanPrivateIdentifier(self):
        start = self.index
        
        # Consume the '#'
        self.index += 1
        
        # The next character must start an identifier
        if self.eof() or not Character.isIdentifierStart(self.source[self.index]):
            self.throwUnexpectedToken()
        
        # Scan the identifier part
        id = self.getIdentifier()
        
        return RawToken(
            type=Token.PrivateIdentifier,
            value='#' + id,
            lineNumber=self.lineNumber,
            lineStart=self.lineStart,
            start=start,
            end=self.index
        )

    def scanHashbang(self):
        start = self.index
        
        # Consume '#!'
        self.index += 2
        
        # Consume the rest of the line
        while not self.eof():
            ch = self.source[self.index]
            if Character.isLineTerminator(ch):
                break
            self.index += 1
        
        # Hashbangs are treated as comments and skipped
        # Advance past the line terminator if present
        if not self.eof() and Character.isLineTerminator(self.source[self.index]):
            if self.source[self.index] == '\r' and self.source[self.index + 1] == '\n':
                self.index += 2
            else:
                self.index += 1
            self.lineNumber += 1
            self.lineStart = self.index
        
        # Return the next actual token
        return self.lex()

    # https://tc39.github.io/ecma262/#sec-punctuators

    def scanPunctuator(self):
        start = self.index

        # Check for most common single-character punctuators.
        str = self.source[self.index]
        if str in (
            '(',
            '{',
        ):
            if str == '{':
                self.curlyStack.append('{')

            self.index += 1

        elif str == '.':
            self.index += 1
            if self.source[self.index] == '.' and self.source[self.index + 1] == '.':
                # Spread operator: ...
                self.index += 2
                str = '...'

        elif str == '}':
            self.index += 1
            if self.curlyStack:
                self.curlyStack.pop()

        elif str in (
            ')',
            ';',
            ',',
            '[',
            ']',
            ':',
            '~',
        ):
            self.index += 1

        elif str == '?':
            # Check for nullish coalescing assignment operator (??=) - ES2021
            if (self.index + 2 < self.length and 
                self.source[self.index + 1:self.index + 3] == '?='):  # ES2021 nullish assignment - always enabled
                self.index += 3
                str = '??='
            # Check for nullish coalescing operator (??) - ES2020, always enabled
            elif (self.index + 1 < self.length and 
                  self.source[self.index + 1] == '?'):
                self.index += 2
                str = '??'
            # Check for optional chaining operator (?.) - ES2020, always enabled
            elif (self.index + 1 < self.length and 
                  self.source[self.index + 1] == '.'):
                # Only if not followed by a digit (to avoid confusion with ?.123)
                if (self.index + 2 >= self.length or 
                    not Character.isDecimalDigit(self.source[self.index + 2])):
                    self.index += 2
                    str = '?.'
                else:
                    self.index += 1
            else:
                self.index += 1

        else:
            # 4-character punctuator.
            str = self.source[self.index:self.index + 4]
            if str == '>>>=':
                self.index += 4
            else:

                # 3-character punctuators.
                str = str[:3]
                if str in (
                    '===', '!==', '>>>',
                    '<<=', '>>=', '**=',
                ):
                    self.index += 3
                else:

                    # 2-character punctuators.
                    str = str[:2]
                    if str in (
                        '==', '!=',
                        '+=', '-=', '*=', '/=',
                        '++', '--', '<<', '>>',
                        '^=', '%=',
                        '<=', '>=', '=>', '**',
                    ):
                        self.index += 2
                    else:

                        # 1-character punctuators.
                        str = self.source[self.index]
                        if str in '<>=!+-*%^/':
                            self.index += 1
                        elif str == '&':
                            # Check for logical assignment &&= (ES2021), always enabled
                            if self.source[self.index + 1:self.index + 3] == '&=':
                                str = '&&='
                                self.index += 3
                            elif self.source[self.index + 1] == '&':
                                str = '&&'
                                self.index += 2
                            elif self.source[self.index + 1] == '=':
                                str = '&='
                                self.index += 2
                            else:
                                self.index += 1
                        elif str == '|':
                            # Check for logical assignment ||= (ES2021), always enabled
                            if self.source[self.index + 1:self.index + 3] == '|=':
                                str = '||='
                                self.index += 3
                            elif self.source[self.index + 1] == '|':
                                str = '||'
                                self.index += 2
                            elif self.source[self.index + 1] == '=':
                                str = '|='
                                self.index += 2
                            else:
                                self.index += 1

        if self.index == start:
            self.throwUnexpectedToken()

        return RawToken(
            type=Token.Punctuator,
            value=str,
            lineNumber=self.lineNumber,
            lineStart=self.lineStart,
            start=start,
            end=self.index
        )

    # https://tc39.github.io/ecma262/#sec-literals-numeric-literals

    def scanNumericSeparatorDigits(self, isDigit, allowEmpty=False, seenDigit=False):
        num = ''

        while not self.eof():
            ch = self.source[self.index]
            if isDigit(ch):
                num += ch
                self.index += 1
                seenDigit = True
            elif ch == '_':
                next = self.source[self.index + 1] if self.index + 1 < self.length else ''
                if not seenDigit or not isDigit(next):
                    self.throwUnexpectedToken()
                self.index += 1
            else:
                break

        if not allowEmpty and not num:
            self.throwUnexpectedToken()

        return num

    def scanHexLiteral(self, start):
        num = self.scanNumericSeparatorDigits(Character.isHexDigit)

        # Check for BigInt literal (ES2020)
        if not self.eof() and self.source[self.index] == 'n':
            self.index += 1  # consume 'n'
            return RawToken(
                type=Token.BigIntLiteral,
                value=int(num, 16),
                raw='0x' + num + 'n',
                lineNumber=self.lineNumber,
                lineStart=self.lineStart,
                start=start,
                end=self.index
            )

        if Character.isIdentifierStart(self.source[self.index]):
            self.throwUnexpectedToken()

        return RawToken(
            type=Token.NumericLiteral,
            value=int(num, 16),
            lineNumber=self.lineNumber,
            lineStart=self.lineStart,
            start=start,
            end=self.index
        )

    def scanBinaryLiteral(self, start):
        num = self.scanNumericSeparatorDigits(lambda ch: ch == '0' or ch == '1')

        # Check for BigInt literal (ES2020)
        if not self.eof() and self.source[self.index] == 'n':
            self.index += 1  # consume 'n'
            return RawToken(
                type=Token.BigIntLiteral,
                value=int(num, 2),
                raw='0b' + num + 'n',
                lineNumber=self.lineNumber,
                lineStart=self.lineStart,
                start=start,
                end=self.index
            )

        if not self.eof():
            ch = self.source[self.index]
            if Character.isIdentifierStart(ch) or Character.isDecimalDigit(ch):
                self.throwUnexpectedToken()

        return RawToken(
            type=Token.NumericLiteral,
            value=int(num, 2),
            lineNumber=self.lineNumber,
            lineStart=self.lineStart,
            start=start,
            end=self.index
        )

    def scanOctalLiteral(self, prefix, start):
        num = ''
        octal = False

        if Character.isOctalDigit(prefix[0]):
            octal = True
            num = '0' + self.source[self.index]
            self.index += 1
            while not self.eof():
                if not Character.isOctalDigit(self.source[self.index]):
                    break

                num += self.source[self.index]
                self.index += 1
        else:
            self.index += 1
            num = self.scanNumericSeparatorDigits(Character.isOctalDigit)

        # Check for BigInt literal (ES2020)
        if not self.eof() and self.source[self.index] == 'n':
            if octal:
                self.throwUnexpectedToken()
            self.index += 1  # consume 'n'
            # Determine the correct raw format
            # New octal like 0o777 -> 0o777n or 0O777 -> 0O777n
            raw = '0' + prefix + num + 'n'
            return RawToken(
                type=Token.BigIntLiteral,
                value=int(num, 8),
                raw=raw,
                lineNumber=self.lineNumber,
                lineStart=self.lineStart,
                start=start,
                end=self.index
            )

        if Character.isIdentifierStart(self.source[self.index]) or Character.isDecimalDigit(self.source[self.index]):
            self.throwUnexpectedToken()

        return RawToken(
            type=Token.NumericLiteral,
            value=int(num, 8),
            octal=octal,
            lineNumber=self.lineNumber,
            lineStart=self.lineStart,
            start=start,
            end=self.index
        )

    def isImplicitOctalLiteral(self):
        # Implicit octal, unless there is a non-octal digit.
        # (Annex B.1.1 on Numeric Literals)
        for i in range(self.index + 1, self.length):
            ch = self.source[i]
            if ch in '89':
                return False
            if not Character.isOctalDigit(ch):
                return True
        return True

    def scanNumericLiteral(self):
        start = self.index
        ch = self.source[start]
        assert Character.isDecimalDigit(ch) or ch == '.', 'Numeric literal must start with a decimal digit or a decimal point'

        num = ''
        if ch != '.':
            num = self.source[self.index]
            self.index += 1
            ch = self.source[self.index]

            # Hex number starts with '0x'.
            # Octal number starts with '0'.
            # Octal number in ES6 starts with '0o'.
            # Binary number in ES6 starts with '0b'.
            if num == '0':
                if ch in ('x', 'X'):
                    self.index += 1
                    return self.scanHexLiteral(start)

                if ch in ('b', 'B'):
                    self.index += 1
                    return self.scanBinaryLiteral(start)

                if ch in ('o', 'O'):
                    return self.scanOctalLiteral(ch, start)

                if ch and Character.isOctalDigit(ch):
                    if self.isImplicitOctalLiteral():
                        return self.scanOctalLiteral(ch, start)

                if ch == '_':
                    self.throwUnexpectedToken()

            num += self.scanNumericSeparatorDigits(Character.isDecimalDigit, allowEmpty=True, seenDigit=bool(num))

            ch = self.source[self.index]

        if ch == '.':
            num += self.source[self.index]
            self.index += 1
            num += self.scanNumericSeparatorDigits(Character.isDecimalDigit, allowEmpty=True)

            ch = self.source[self.index]

        if ch in ('e', 'E'):
            num += self.source[self.index]
            self.index += 1

            ch = self.source[self.index]
            if ch in ('+', '-'):
                num += self.source[self.index]
                self.index += 1

            if Character.isDecimalDigit(self.source[self.index]):
                num += self.scanNumericSeparatorDigits(Character.isDecimalDigit, allowEmpty=True)

            else:
                self.throwUnexpectedToken()

        # Check for BigInt literal (ES2020)
        if self.source[self.index] == 'n':
            # BigInt literals cannot have decimals or exponents
            if '.' in num or 'e' in num.lower() or (len(num) > 1 and num[0] == '0'):
                self.throwUnexpectedToken()
            
            # ES2020+ BigInt support - always enabled
            self.index += 1  # consume 'n'
            # BigInt value: convert string to int for storage
            try:
                bigint_value = int(num)
            except ValueError:
                self.throwUnexpectedToken()
            
            return RawToken(
                type=Token.BigIntLiteral,
                value=bigint_value,
                raw=num + 'n',
                lineNumber=self.lineNumber,
                lineStart=self.lineStart,
                start=start,
                end=self.index
            )

        if Character.isIdentifierStart(self.source[self.index]):
            self.throwUnexpectedToken()

        value = float(num)
        return RawToken(
            type=Token.NumericLiteral,
            value=int(value) if value.is_integer() else value,
            lineNumber=self.lineNumber,
            lineStart=self.lineStart,
            start=start,
            end=self.index
        )

    # https://tc39.github.io/ecma262/#sec-literals-string-literals

    def scanStringLiteral(self):
        start = self.index
        quote = self.source[start]
        assert quote in ('\'', '"'), 'String literal must starts with a quote'

        self.index += 1
        octal = False
        # List + join: `str += ch` here is O(n^2) in CPython; `list +=` extends by char.
        str = []

        while not self.eof():
            ch = self.source[self.index]
            self.index += 1

            if ch == quote:
                quote = ''
                break
            elif ch == '\\':
                ch = self.source[self.index]
                self.index += 1
                if not ch or not Character.isLineTerminator(ch):
                    if ch == 'u':
                        if self.source[self.index] == '{':
                            self.index += 1
                            str += self.scanUnicodeCodePointEscape()
                        else:
                            unescapedChar = self.scanHexEscape(ch)
                            if not unescapedChar:
                                self.throwUnexpectedToken()

                            str += unescapedChar

                    elif ch == 'x':
                        unescaped = self.scanHexEscape(ch)
                        if not unescaped:
                            self.throwUnexpectedToken(Messages.InvalidHexEscapeSequence)

                        str += unescaped
                    elif ch == 'n':
                        str += '\n'
                    elif ch == 'r':
                        str += '\r'
                    elif ch == 't':
                        str += '\t'
                    elif ch == 'b':
                        str += '\b'
                    elif ch == 'f':
                        str += '\f'
                    elif ch == 'v':
                        str += '\x0B'
                    elif ch in (
                        '8',
                        '9',
                    ):
                        str += ch
                        self.tolerateUnexpectedToken()

                    else:
                        if ch and Character.isOctalDigit(ch):
                            octToDec = self.octalToDecimal(ch)

                            octal = octToDec.octal or octal
                            str += chr(octToDec.code)
                        else:
                            str += ch

                else:
                    self.lineNumber += 1
                    if ch == '\r' and self.source[self.index] == '\n':
                        self.index += 1

                    self.lineStart = self.index

            elif Character.isLineTerminator(ch):
                break
            else:
                str += ch

        if quote != '':
            self.index = start
            self.throwUnexpectedToken()

        return RawToken(
            type=Token.StringLiteral,
            value=''.join(str),
            octal=octal,
            lineNumber=self.lineNumber,
            lineStart=self.lineStart,
            start=start,
            end=self.index
        )

    # https://tc39.github.io/ecma262/#sec-template-literal-lexical-components

    def scanTemplate(self):
        # List + join, as in scanStringLiteral, to keep this linear.
        cooked = []
        terminated = False
        start = self.index

        head = self.source[start] == '`'
        tail = False
        rawOffset = 2

        self.index += 1

        while not self.eof():
            ch = self.source[self.index]
            self.index += 1
            if ch == '`':
                rawOffset = 1
                tail = True
                terminated = True
                break
            elif ch == '$':
                if self.source[self.index] == '{':
                    self.curlyStack.append('${')
                    self.index += 1
                    terminated = True
                    break

                cooked += ch
            elif ch == '\\':
                ch = self.source[self.index]
                self.index += 1
                if not Character.isLineTerminator(ch):
                    if ch == 'n':
                        cooked += '\n'
                    elif ch == 'r':
                        cooked += '\r'
                    elif ch == 't':
                        cooked += '\t'
                    elif ch == 'u':
                        if self.source[self.index] == '{':
                            self.index += 1
                            cooked += self.scanUnicodeCodePointEscape()
                        else:
                            restore = self.index
                            unescapedChar = self.scanHexEscape(ch)
                            if unescapedChar:
                                cooked += unescapedChar
                            else:
                                self.index = restore
                                cooked += ch

                    elif ch == 'x':
                        unescaped = self.scanHexEscape(ch)
                        if not unescaped:
                            self.throwUnexpectedToken(Messages.InvalidHexEscapeSequence)

                        cooked += unescaped
                    elif ch == 'b':
                        cooked += '\b'
                    elif ch == 'f':
                        cooked += '\f'
                    elif ch == 'v':
                        cooked += '\v'

                    else:
                        if ch == '0':
                            if Character.isDecimalDigit(self.source[self.index]):
                                # Illegal: \01 \02 and so on
                                self.throwUnexpectedToken(Messages.TemplateOctalLiteral)

                            cooked += '\0'
                        elif Character.isOctalDigit(ch):
                            # Illegal: \1 \2
                            self.throwUnexpectedToken(Messages.TemplateOctalLiteral)
                        else:
                            cooked += ch

                else:
                    self.lineNumber += 1
                    if ch == '\r' and self.source[self.index] == '\n':
                        self.index += 1

                    self.lineStart = self.index

            elif Character.isLineTerminator(ch):
                self.lineNumber += 1
                if ch == '\r' and self.source[self.index] == '\n':
                    self.index += 1

                self.lineStart = self.index
                cooked += '\n'
            else:
                cooked += ch

        if not terminated:
            self.throwUnexpectedToken()

        if not head:
            if self.curlyStack:
                self.curlyStack.pop()

        return RawToken(
            type=Token.Template,
            value=self.source[start + 1:self.index - rawOffset],
            cooked=''.join(cooked),
            head=head,
            tail=tail,
            lineNumber=self.lineNumber,
            lineStart=self.lineStart,
            start=start,
            end=self.index
        )

    # https://tc39.github.io/ecma262/#sec-literals-regular-expression-literals

    def validateRegExpFlags(self, flags):
        allowed = set('dgimsuvy')
        seen = set()
        for flag in flags:
            if flag in seen or flag not in allowed:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return
            seen.add(flag)

        if 'u' in seen and 'v' in seen:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)

    def readRegExpIdentifierEscape(self, name, index):
        length = len(name)
        if index + 1 >= length or name[index + 1] != 'u':
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return index + 1, None

        if index + 2 < length and name[index + 2] == '{':
            i = index + 3
            start = i
            while i < length and name[i] != '}':
                if not Character.isHexDigit(name[i]):
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                    return i + 1, None
                i += 1

            if i == start or i >= length:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return i, None

            codePoint = int(name[start:i], 16)
            if codePoint > 0x10FFFF:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return i + 1, None

            return i + 1, Character.fromCodePoint(codePoint)

        if index + 5 >= length:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return length, None

        digits = name[index + 2:index + 6]
        for ch in digits:
            if not Character.isHexDigit(ch):
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return index + 6, None

        codePoint = int(digits, 16)
        end = index + 6
        if 0xD800 <= codePoint <= 0xDBFF and end + 5 < length and name[end:end + 2] == '\\u':
            lowDigits = name[end + 2:end + 6]
            if all(Character.isHexDigit(ch) for ch in lowDigits):
                lowSurrogate = int(lowDigits, 16)
                if 0xDC00 <= lowSurrogate <= 0xDFFF:
                    codePoint = 0x10000 + (codePoint - 0xD800) * 0x400 + (lowSurrogate - 0xDC00)
                    end += 6

        return end, Character.fromCodePoint(codePoint)

    def validateRegExpIdentifierName(self, name):
        normalized = ''
        i = 0
        length = len(name)

        while i < length:
            if name[i] == '\\':
                i, ch = self.readRegExpIdentifierEscape(name, i)
                if ch is None:
                    return False
            else:
                ch = name[i]
                i += 1

            if not normalized:
                if not self.isRegExpIdentifierStart(ch):
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                    return False
            elif not self.isRegExpIdentifierPart(ch):
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return False

            normalized += ch

        if not normalized:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return False

        return normalized

    def regExpGroupsCanBothParticipate(self, left, right):
        rightMap = dict(right)
        for contextId, alternative in left:
            if contextId in rightMap and rightMap[contextId] != alternative:
                return False
        return True

    def validateRegExpGroupName(self, names, name, path):
        normalizedName = self.validateRegExpIdentifierName(name)
        if not normalizedName:
            return

        for otherPath in names.get(normalizedName, []):
            if self.regExpGroupsCanBothParticipate(otherPath, path):
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return

        names.setdefault(normalizedName, []).append(path)

    def isRegExpIdentifierStart(self, ch):
        return ch != '\\' and (
            Character.isIdentifierStart(ch) or
            unicodedata.category(ch) in ('Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nl')
        )

    def isRegExpIdentifierPart(self, ch):
        return ch != '\\' and (
            self.isRegExpIdentifierStart(ch) or
            Character.isIdentifierPart(ch) or
            unicodedata.category(ch) in ('Mn', 'Mc', 'Nd', 'Pc')
        )

    def validateRegExpModifiers(self, enabling, disabling):
        if not enabling and disabling is not None and not disabling:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return

        enabled = set()
        for flag in enabling:
            if flag in enabled:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return
            enabled.add(flag)

        disabled = set()
        for flag in disabling or '':
            if flag in disabled or flag in enabled:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return
            disabled.add(flag)

    def normalizeRegExpModifiers(self, enabling, disabling):
        if disabling is None or not disabling:
            return '(?%s:' % enabling
        if not enabling:
            return '(?-%s:' % disabling
        return '(?%s-%s:' % (enabling, disabling)

    def scanRegExpModifiers(self, pattern, index):
        length = len(pattern)
        i = index
        enabling = ''

        while i < length and pattern[i] in 'ims':
            enabling += pattern[i]
            i += 1

        if i < length and pattern[i] == '-':
            i += 1
            disabling = ''
            while i < length and pattern[i] in 'ims':
                disabling += pattern[i]
                i += 1
            if i < length and pattern[i] == ':':
                self.validateRegExpModifiers(enabling, disabling)
                return i + 1, self.normalizeRegExpModifiers(enabling, disabling)
            return None

        if i < length and pattern[i] == ':':
            self.validateRegExpModifiers(enabling, None)
            return i + 1, self.normalizeRegExpModifiers(enabling, None)

        return None

    def validateRegExpUnicodeProperty(self, expression, negative, unicodeSetsMode):
        if not expression:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return False

        mayContainStrings = False
        parts = expression.split('=')
        if len(parts) == 2:
            name, value = parts
            if name not in REGEXP_UNICODE_PROPERTY_NAMES:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            elif name in ('General_Category', 'gc'):
                if value not in REGEXP_GENERAL_CATEGORY_VALUES:
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            elif value not in REGEXP_SCRIPT_VALUES:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
        elif len(parts) == 1:
            mayContainStrings = expression in REGEXP_BINARY_PROPERTIES_OF_STRINGS
            if expression not in REGEXP_GENERAL_CATEGORY_VALUES and expression not in REGEXP_BINARY_UNICODE_PROPERTIES and not mayContainStrings:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            elif mayContainStrings and (negative or not unicodeSetsMode):
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
        else:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)

        return mayContainStrings

    def validateRegExpUnicodePropertyEscape(self, pattern, index, unicodeSetsMode, returnMayContainStrings=False):
        if index + 2 >= len(pattern) or pattern[index] != '\\' or pattern[index + 1] not in ('p', 'P') or pattern[index + 2] != '{':
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return (index + 2, False) if returnMayContainStrings else index + 2

        close = pattern.find('}', index + 3)
        if close == -1:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return (index + 2, False) if returnMayContainStrings else index + 2

        mayContainStrings = self.validateRegExpUnicodeProperty(pattern[index + 3:close], pattern[index + 1] == 'P', unicodeSetsMode)
        return (close + 1, mayContainStrings) if returnMayContainStrings else close + 1

    def skipRegExpBracedEscape(self, pattern, index):
        i = index + 3
        length = len(pattern)
        while i < length:
            ch = pattern[i]
            if ch == '\\':
                if i + 2 < length and pattern[i + 1] == 'u' and pattern[i + 2] == '{':
                    close = pattern.find('}', i + 3)
                    if close == -1:
                        self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                        return i + 2
                    i = close + 1
                else:
                    i += 2
                continue
            if ch == '}':
                return i + 1
            i += 1

        if i >= length:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return index + 2
        return i

    def skipRegExpUnicodeEscape(self, pattern, index):
        if index + 2 < len(pattern) and pattern[index + 2] == '{':
            close = pattern.find('}', index + 3)
            if close == -1:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return index + 2
            return close + 1
        return index + 2

    def validateRegExpBracedQuantifier(self, pattern, index):
        i = index + 1
        length = len(pattern)
        if i >= length or not Character.isDecimalDigit(pattern[i]):
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return index + 1

        minimumStart = i
        while i < length and Character.isDecimalDigit(pattern[i]):
            i += 1
        minimum = int(pattern[minimumStart:i])

        if i < length and pattern[i] == '}':
            return i + 1

        if i < length and pattern[i] == ',':
            i += 1
            maximumStart = i
            while i < length and Character.isDecimalDigit(pattern[i]):
                i += 1
            if i < length and pattern[i] == '}':
                if maximumStart != i and minimum > int(pattern[maximumStart:i]):
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return i + 1

        self.tolerateUnexpectedToken(Messages.InvalidRegExp)
        return index + 1

    def readRegExpBracedQuantifier(self, pattern, index):
        i = index + 1
        length = len(pattern)
        if i >= length or not Character.isDecimalDigit(pattern[i]):
            return None

        minimumStart = i
        while i < length and Character.isDecimalDigit(pattern[i]):
            i += 1
        minimum = int(pattern[minimumStart:i])

        if i < length and pattern[i] == '}':
            return i + 1

        if i < length and pattern[i] == ',':
            i += 1
            maximumStart = i
            while i < length and Character.isDecimalDigit(pattern[i]):
                i += 1
            if i < length and pattern[i] == '}':
                if maximumStart != i and minimum > int(pattern[maximumStart:i]):
                    return None
                return i + 1

        return None

    def readRegExpBracedQuantifierSyntax(self, pattern, index):
        i = index + 1
        length = len(pattern)
        if i >= length or not Character.isDecimalDigit(pattern[i]):
            return None

        while i < length and Character.isDecimalDigit(pattern[i]):
            i += 1

        if i < length and pattern[i] == '}':
            return i + 1

        if i < length and pattern[i] == ',':
            i += 1
            while i < length and Character.isDecimalDigit(pattern[i]):
                i += 1
            if i < length and pattern[i] == '}':
                return i + 1

        return None

    def validateRegExpBracedQuantifiers(self, pattern):
        i = 0
        length = len(pattern)
        classDepth = 0

        while i < length:
            ch = pattern[i]

            if classDepth > 0:
                if ch == '\\':
                    if i + 2 < length and pattern[i + 1] == 'q' and pattern[i + 2] == '{':
                        i = self.skipRegExpBracedEscape(pattern, i)
                    else:
                        i += 2
                    continue
                if ch == '[':
                    classDepth += 1
                    i += 1
                    continue
                if ch == ']':
                    classDepth -= 1
                i += 1
                continue

            if ch == '\\':
                if i + 2 < length and pattern[i + 1] in ('p', 'P') and pattern[i + 2] == '{':
                    i = self.skipRegExpBracedEscape(pattern, i)
                elif i + 1 < length and pattern[i + 1] == 'u':
                    i = self.skipRegExpUnicodeEscape(pattern, i)
                else:
                    i += 2
                continue

            if ch == '[':
                classDepth = 1
                i += 1
                continue

            if ch == '{':
                i = self.validateRegExpBracedQuantifier(pattern, i)
                continue

            i += 1

    def validateRegExpQuantifierSuffixes(self, pattern, unicodeMode=True):
        i = 0
        length = len(pattern)
        classDepth = 0

        def validateSuffix(end):
            if end < length and pattern[end] == '?':
                end += 1
            if end < length and pattern[end] in '*+?':
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            elif end < length and pattern[end] == '{':
                if unicodeMode or self.readRegExpBracedQuantifierSyntax(pattern, end) is not None:
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)

        while i < length:
            ch = pattern[i]

            if classDepth > 0:
                if ch == '\\':
                    if i + 2 < length and pattern[i + 1] == 'q' and pattern[i + 2] == '{':
                        i = self.skipRegExpBracedEscape(pattern, i)
                    else:
                        i += 2
                    continue
                if ch == '[':
                    classDepth += 1
                    i += 1
                    continue
                if ch == ']':
                    classDepth -= 1
                i += 1
                continue

            if ch == '\\':
                if unicodeMode and i + 2 < length and pattern[i + 1] in ('p', 'P') and pattern[i + 2] == '{':
                    i = self.skipRegExpBracedEscape(pattern, i)
                elif unicodeMode and i + 1 < length and pattern[i + 1] == 'u':
                    i = self.skipRegExpUnicodeEscape(pattern, i)
                else:
                    i += 2
                continue

            if ch == '[':
                classDepth = 1
                i += 1
                continue

            if ch in '*+?':
                validateSuffix(i + 1)
                i += 1
                continue

            if ch == '{':
                if unicodeMode:
                    end = self.validateRegExpBracedQuantifier(pattern, i)
                else:
                    end = self.readRegExpBracedQuantifier(pattern, i)
                    if end is None:
                        i += 1
                        continue
                validateSuffix(end)
                i = end
                continue

            i += 1

    def hasRegExpNamedCapturingGroup(self, pattern, unicodeMode=True):
        i = 0
        length = len(pattern)
        classDepth = 0

        while i < length:
            ch = pattern[i]

            if classDepth > 0:
                if ch == '\\':
                    if i + 2 < length and pattern[i + 1] == 'q' and pattern[i + 2] == '{':
                        i = self.skipRegExpBracedEscape(pattern, i)
                    else:
                        i += 2
                    continue
                if ch == '[':
                    classDepth += 1
                    i += 1
                    continue
                if ch == ']':
                    classDepth -= 1
                i += 1
                continue

            if ch == '\\':
                if unicodeMode and i + 2 < length and pattern[i + 1] in ('p', 'P') and pattern[i + 2] == '{':
                    i = self.skipRegExpBracedEscape(pattern, i)
                elif unicodeMode and i + 1 < length and pattern[i + 1] == 'u':
                    i = self.skipRegExpUnicodeEscape(pattern, i)
                else:
                    i += 2
                continue

            if ch == '[':
                classDepth = 1
                i += 1
                continue

            if pattern.startswith('(?<', i) and i + 3 < length and pattern[i + 3] not in ('=', '!'):
                return True

            i += 1

        return False

    def countRegExpCapturingGroups(self, pattern):
        count = 0
        i = 0
        length = len(pattern)
        classDepth = 0

        while i < length:
            ch = pattern[i]

            if classDepth > 0:
                if ch == '\\':
                    if i + 2 < length and pattern[i + 1] == 'q' and pattern[i + 2] == '{':
                        i = self.skipRegExpBracedEscape(pattern, i)
                    else:
                        i += 2
                    continue
                if ch == '[':
                    classDepth += 1
                    i += 1
                    continue
                if ch == ']':
                    classDepth -= 1
                i += 1
                continue

            if ch == '\\':
                if i + 2 < length and pattern[i + 1] in ('p', 'P') and pattern[i + 2] == '{':
                    i = self.skipRegExpBracedEscape(pattern, i)
                elif i + 1 < length and pattern[i + 1] == 'u':
                    i = self.skipRegExpUnicodeEscape(pattern, i)
                else:
                    i += 2
                continue

            if ch == '[':
                classDepth = 1
                i += 1
                continue

            if ch == '(':
                if pattern.startswith('(?<', i):
                    if i + 3 < length and pattern[i + 3] not in ('=', '!'):
                        count += 1
                elif not pattern.startswith('(?', i):
                    count += 1
                i += 1
                continue

            i += 1

        return count

    def sanitizeRegExpNumericBackreferences(self, pattern, captureCount):
        output = []
        i = 0
        length = len(pattern)
        classDepth = 0

        while i < length:
            ch = pattern[i]

            if classDepth > 0:
                if ch == '\\':
                    if i + 2 < length and pattern[i + 1] in ('p', 'P', 'q') and pattern[i + 2] == '{':
                        end = self.skipRegExpBracedEscape(pattern, i)
                        output.append(pattern[i:end])
                        i = end
                    else:
                        output.append(pattern[i:i + 2])
                        i += 2
                    continue
                output.append(ch)
                if ch == '[':
                    classDepth += 1
                elif ch == ']':
                    classDepth -= 1
                i += 1
                continue

            if ch == '\\':
                if i + 1 < length and pattern[i + 1] in '123456789':
                    end = i + 2
                    while end < length and Character.isDecimalDigit(pattern[end]):
                        end += 1
                    if int(pattern[i + 1:end]) > captureCount:
                        self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                    output.append('(?:)')
                    i = end
                    continue

                output.append(pattern[i:i + 2])
                i += 2
                continue

            if ch == '[':
                classDepth = 1

            output.append(ch)
            i += 1

        return ''.join(output)

    def isRegExpQuantifierStart(self, pattern, index):
        return index < len(pattern) and pattern[index] in '*+?{'

    def skipRegExpGroup(self, pattern, index):
        i = index + 1
        length = len(pattern)
        groupDepth = 1
        classDepth = 0

        while i < length and groupDepth > 0:
            ch = pattern[i]

            if classDepth > 0:
                if ch == '\\':
                    if i + 2 < length and pattern[i + 1] == 'q' and pattern[i + 2] == '{':
                        i = self.skipRegExpBracedEscape(pattern, i)
                    else:
                        i += 2
                    continue
                if ch == '[':
                    classDepth += 1
                    i += 1
                    continue
                if ch == ']':
                    classDepth -= 1
                i += 1
                continue

            if ch == '\\':
                if i + 2 < length and pattern[i + 1] in ('p', 'P') and pattern[i + 2] == '{':
                    i = self.skipRegExpBracedEscape(pattern, i)
                elif i + 1 < length and pattern[i + 1] == 'u':
                    i = self.skipRegExpUnicodeEscape(pattern, i)
                else:
                    i += 2
                continue

            if ch == '[':
                classDepth = 1
                i += 1
                continue

            if ch == '(':
                groupDepth += 1
                i += 1
                continue

            if ch == ')':
                groupDepth -= 1
                i += 1
                continue

            i += 1

        if groupDepth > 0:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)

        return i

    def validateRegExpAssertionQuantifiers(self, pattern):
        i = 0
        length = len(pattern)
        classDepth = 0

        while i < length:
            ch = pattern[i]

            if classDepth > 0:
                if ch == '\\':
                    if i + 2 < length and pattern[i + 1] == 'q' and pattern[i + 2] == '{':
                        i = self.skipRegExpBracedEscape(pattern, i)
                    else:
                        i += 2
                    continue
                if ch == '[':
                    classDepth += 1
                    i += 1
                    continue
                if ch == ']':
                    classDepth -= 1
                i += 1
                continue

            if ch == '\\':
                end = i + 2
                if i + 1 < length and pattern[i + 1] in 'bB' and self.isRegExpQuantifierStart(pattern, end):
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                if i + 2 < length and pattern[i + 1] in ('p', 'P') and pattern[i + 2] == '{':
                    i = self.skipRegExpBracedEscape(pattern, i)
                elif i + 1 < length and pattern[i + 1] == 'u':
                    i = self.skipRegExpUnicodeEscape(pattern, i)
                else:
                    i = end
                continue

            if ch == '[':
                classDepth = 1
                i += 1
                continue

            if ch in '^$':
                if self.isRegExpQuantifierStart(pattern, i + 1):
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                i += 1
                continue

            if pattern.startswith(('(?=', '(?!'), i) or pattern.startswith(('(?<=', '(?<!'), i):
                end = self.skipRegExpGroup(pattern, i)
                if self.isRegExpQuantifierStart(pattern, end):
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                i += 1
                continue

            i += 1

    def validateLegacyRegExpLookbehindQuantifiers(self, pattern):
        i = 0
        length = len(pattern)
        classDepth = 0

        while i < length:
            ch = pattern[i]

            if classDepth > 0:
                if ch == '\\':
                    i += 2
                    continue
                if ch == '[':
                    classDepth += 1
                    i += 1
                    continue
                if ch == ']':
                    classDepth -= 1
                i += 1
                continue

            if ch == '\\':
                i += 2
                continue

            if ch == '[':
                classDepth = 1
                i += 1
                continue

            if pattern.startswith(('(?<=', '(?<!'), i):
                end = self.skipRegExpGroup(pattern, i)
                if end < length and pattern[end] in '*+?':
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                if end < length and self.readRegExpBracedQuantifierSyntax(pattern, end) is not None:
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                i = end
                continue

            i += 1

    def sanitizeRegExpCodePoint(self, codePoint):
        if codePoint > 0xFFFF:
            return chr(codePoint)
        if codePoint <= 0xFF:
            return '\\x%02x' % codePoint
        return '\\u%04x' % codePoint

    def scanRegExpUnicodeEscapeSequence(self, pattern, index, inClass=False, unicodeSetsMode=False):
        length = len(pattern)
        if index + 1 >= length:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return index + 1, 'a'

        escaped = pattern[index + 1]

        if escaped in 'fntvr':
            return index + 2, '\\' + escaped

        if escaped in '123456789':
            if inClass:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            end = index + 2
            while end < length and Character.isDecimalDigit(pattern[end]):
                end += 1
            return end, pattern[index:end]

        if escaped == '0':
            if index + 2 < length and Character.isDecimalDigit(pattern[index + 2]):
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return index + 2, '\\0'

        if escaped == 'b':
            return index + 2, '\\x08' if inClass else '\\b'

        if escaped == 'B':
            if inClass:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return index + 2, '\\B'

        if escaped in 'dDsSwW':
            return index + 2, '\\' + escaped

        if escaped == 'c':
            if index + 2 < length and pattern[index + 2] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
                value = ord(pattern[index + 2].upper()) - ord('A') + 1
                return index + 3, '\\x%02x' % value
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return index + 2, 'a'

        if escaped == 'x':
            if index + 3 < length and Character.isHexDigit(pattern[index + 2]) and Character.isHexDigit(pattern[index + 3]):
                return index + 4, '\\x' + pattern[index + 2:index + 4]
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return min(index + 2, length), 'a'

        if escaped == 'u':
            if index + 2 < length and pattern[index + 2] == '{':
                i = index + 3
                start = i
                while i < length and pattern[i] != '}':
                    if not Character.isHexDigit(pattern[i]):
                        self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                        return i + 1, 'a'
                    i += 1
                if i == start or i >= length:
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                    return i, 'a'
                codePoint = int(pattern[start:i], 16)
                if codePoint > 0x10FFFF:
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                    return i + 1, 'a'
                return i + 1, self.sanitizeRegExpCodePoint(codePoint)

            if index + 5 < length:
                digits = pattern[index + 2:index + 6]
                if all(Character.isHexDigit(ch) for ch in digits):
                    return index + 6, self.sanitizeRegExpCodePoint(int(digits, 16))

            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return min(index + 2, length), 'a'

        if escaped in ('p', 'P') and index + 2 < length and pattern[index + 2] == '{':
            end = self.validateRegExpUnicodePropertyEscape(pattern, index, unicodeSetsMode)
            if inClass and not unicodeSetsMode:
                return end, '\\D' if escaped == 'P' else '\\d'
            return end, '.'

        if escaped == '-' and inClass:
            return index + 2, '\\x2d'

        if unicodeSetsMode and inClass:
            for punctuator in REGEXP_CLASS_SET_RESERVED_DOUBLE_PUNCTUATORS:
                if escaped in punctuator:
                    return index + 2, '\\' + escaped

        if escaped in REGEXP_IDENTITY_ESCAPE_CHARACTERS:
            return index + 2, '\\' + escaped

        self.tolerateUnexpectedToken(Messages.InvalidRegExp)
        return index + 2, 'a'

    def sanitizeRegExpUnicodePattern(self, pattern):
        output = []
        i = 0
        length = len(pattern)
        classDepth = 0

        while i < length:
            ch = pattern[i]

            if ch == '\\':
                end, replacement = self.scanRegExpUnicodeEscapeSequence(pattern, i, classDepth > 0)
                output.append(replacement)
                i = end
                continue

            if ch == '[':
                if classDepth == 0:
                    if i + 1 < length and pattern[i + 1] == ']':
                        output.append('(?!)')
                        i += 2
                        continue
                    if i + 2 < length and pattern[i + 1] == '^' and pattern[i + 2] == ']':
                        output.append('[\\s\\S]')
                        i += 3
                        continue
                    classDepth = 1
            elif ch == ']':
                if classDepth > 0:
                    classDepth = 0
                else:
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            elif ch == '{' and classDepth == 0:
                end = self.validateRegExpBracedQuantifier(pattern, i)
                output.append(pattern[i:end])
                i = end
                continue
            elif ch == '}' and classDepth == 0:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)

            output.append(ch)
            i += 1

        return ''.join(output)

    def prepareRegExpPattern(self, pattern, strictNamedReferences=True):
        names = {}
        references = []
        output = []
        stack = [{'id': 0, 'alternative': 0}]
        nextContextId = 1
        classMarker = False
        i = 0
        length = len(pattern)

        while i < length:
            ch = pattern[i]

            if classMarker:
                if ch == '\\':
                    output.append(pattern[i:i + 2])
                    i += 2
                    continue

                output.append(ch)
                if ch == ']':
                    classMarker = False
                i += 1
                continue

            if ch == '\\':
                if i + 2 < length and pattern[i + 1] == 'k' and pattern[i + 2] == '<':
                    if not strictNamedReferences:
                        output.append('k')
                        i += 2
                        continue

                    end = pattern.find('>', i + 3)
                    if end == -1:
                        self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                        output.append(ch)
                        i += 1
                    else:
                        name = pattern[i + 3:end]
                        normalizedName = self.validateRegExpIdentifierName(name)
                        if normalizedName:
                            references.append(normalizedName)
                        output.append('(?:)')
                        i = end + 1
                    continue

                output.append(pattern[i:i + 2])
                i += 2
                continue

            if ch == '[':
                classMarker = True
                output.append(ch)
                i += 1
                continue

            if ch == '|':
                stack[-1]['alternative'] += 1
                output.append(ch)
                i += 1
                continue

            if ch == ')':
                if len(stack) > 1:
                    stack.pop()
                output.append(ch)
                i += 1
                continue

            if ch == '(':
                if pattern.startswith('(?<', i) and i + 3 < length and pattern[i + 3] not in ('=', '!'):
                    end = pattern.find('>', i + 3)
                    if end == -1:
                        self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                        output.append(ch)
                        i += 1
                        continue

                    name = pattern[i + 3:end]
                    path = tuple((context['id'], context['alternative']) for context in stack)
                    self.validateRegExpGroupName(names, name, path)
                    output.append('(')
                    stack.append({'id': nextContextId, 'alternative': 0})
                    nextContextId += 1
                    i = end + 1
                    continue

                if pattern.startswith('(?', i):
                    modifier = self.scanRegExpModifiers(pattern, i + 2)
                    if modifier is not None:
                        modifierEnd, normalizedModifier = modifier
                        output.append(normalizedModifier)
                        stack.append({'id': nextContextId, 'alternative': 0})
                        nextContextId += 1
                        i = modifierEnd
                        continue

                    if pattern.startswith(('(?=', '(?!'), i):
                        output.append(pattern[i:i + 3])
                        stack.append({'id': nextContextId, 'alternative': 0})
                        nextContextId += 1
                        i += 3
                        continue

                    if pattern.startswith(('(?<=', '(?<!'), i):
                        output.append(pattern[i:i + 4])
                        stack.append({'id': nextContextId, 'alternative': 0})
                        nextContextId += 1
                        i += 4
                        continue

                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)

                output.append(ch)
                stack.append({'id': nextContextId, 'alternative': 0})
                nextContextId += 1
                i += 1
                continue

            output.append(ch)
            i += 1

        for reference in references:
            if reference not in names:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                break

        return ''.join(output)

    def sanitizeRegExpLookbehindAssertions(self, pattern):
        output = []
        i = 0
        length = len(pattern)
        classMarker = False

        while i < length:
            ch = pattern[i]

            if classMarker:
                output.append(ch)
                if ch == '\\' and i + 1 < length:
                    output.append(pattern[i + 1])
                    i += 2
                    continue
                if ch == ']':
                    classMarker = False
                i += 1
                continue

            if ch == '\\':
                output.append(pattern[i:i + 2])
                i += 2
                continue

            if ch == '[':
                classMarker = True
                output.append(ch)
                i += 1
                continue

            if pattern.startswith('(?<=', i):
                output.append('(?=')
                i += 4
                continue

            if pattern.startswith('(?<!', i):
                output.append('(?!')
                i += 4
                continue

            output.append(ch)
            i += 1

        return ''.join(output)

    def sanitizeLegacyRegExpLiteralBracesAfterQuantifiers(self, pattern):
        output = []
        i = 0
        length = len(pattern)
        classDepth = 0

        while i < length:
            ch = pattern[i]

            if classDepth > 0:
                if ch == '\\':
                    output.append(pattern[i:i + 2])
                    i += 2
                    continue
                output.append(ch)
                if ch == '[':
                    classDepth += 1
                elif ch == ']':
                    classDepth -= 1
                i += 1
                continue

            if ch == '\\':
                output.append(pattern[i:i + 2])
                i += 2
                continue

            if ch == '[':
                if i + 1 < length and pattern[i + 1] == ']':
                    output.append('(?!)')
                    i += 2
                    continue
                if i + 2 < length and pattern[i + 1] == '^' and pattern[i + 2] == ']':
                    output.append('[\\s\\S]')
                    i += 3
                    continue
                classDepth = 1
                output.append(ch)
                i += 1
                continue

            quantifierEnd = None
            if ch in '*+?':
                output.append(ch)
                quantifierEnd = i + 1
            elif ch == '{':
                quantifierEnd = self.readRegExpBracedQuantifier(pattern, i)
                if quantifierEnd is None:
                    output.append(ch)
                    i += 1
                    continue
                output.append(pattern[i:quantifierEnd])
            else:
                output.append(ch)
                i += 1
                continue

            i = quantifierEnd
            if i < length and pattern[i] == '?':
                output.append('?')
                i += 1
            if i < length and pattern[i] == '{':
                output.append('\\{')
                i += 1

        return ''.join(output)

    def sanitizeLegacyRegExpPattern(self, pattern):
        output = []
        i = 0
        length = len(pattern)
        classDepth = 0

        def sanitizeClassEscape(index):
            if index + 1 >= length:
                return '\\\\', index + 1

            escaped = pattern[index + 1]
            if escaped == 'c':
                if index + 2 < length and pattern[index + 2] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
                    value = ord(pattern[index + 2].upper()) - ord('A') + 1
                    return '\\x%02x' % value, index + 3
                return 'c', index + 2

            if escaped == 'x':
                if index + 3 < length and Character.isHexDigit(pattern[index + 2]) and Character.isHexDigit(pattern[index + 3]):
                    return pattern[index:index + 4], index + 4
                return 'x', index + 2

            if escaped == 'u':
                if index + 5 < length and all(Character.isHexDigit(ch) for ch in pattern[index + 2:index + 6]):
                    return pattern[index:index + 6], index + 6
                return 'u', index + 2

            if escaped == 'b':
                return '\\x08', index + 2

            if escaped in 'fntvr0':
                return '\\' + escaped, index + 2

            if escaped in 'dDsSwW':
                return 'z' if index > 0 and pattern[index - 1] == '-' else 'a', index + 2

            if escaped in '^$\\.*+?()[]{}|-/':
                return '\\' + escaped if escaped in '\\]^-/' else re.escape(escaped), index + 2

            return re.escape(escaped), index + 2

        while i < length:
            ch = pattern[i]

            if classDepth > 0:
                if ch == '\\':
                    replacement, i = sanitizeClassEscape(i)
                    output.append(replacement)
                    continue
                output.append(ch)
                if ch == '[':
                    classDepth += 1
                elif ch == ']':
                    classDepth -= 1
                i += 1
                continue

            if ch == '[':
                classDepth = 1
                output.append(ch)
                i += 1
                continue

            if ch == '\\':
                if i + 1 >= length:
                    output.append(ch)
                    i += 1
                    continue

                escaped = pattern[i + 1]
                if escaped == 'c':
                    if i + 2 < length and pattern[i + 2] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
                        value = ord(pattern[i + 2].upper()) - ord('A') + 1
                        output.append('\\x%02x' % value)
                        i += 3
                    else:
                        output.append('c')
                        i += 2
                    continue

                if escaped == 'x':
                    if i + 3 < length and Character.isHexDigit(pattern[i + 2]) and Character.isHexDigit(pattern[i + 3]):
                        output.append(pattern[i:i + 4])
                        i += 4
                    else:
                        output.append('x')
                        i += 2
                    continue

                if escaped == 'u':
                    if i + 5 < length and all(Character.isHexDigit(ch) for ch in pattern[i + 2:i + 6]):
                        output.append(pattern[i:i + 6])
                        i += 6
                    else:
                        output.append('u')
                        i += 2
                    continue

                if escaped in 'pP':
                    output.append(escaped)
                    i += 2
                    continue

                if escaped in 'bB':
                    output.append('\\' + escaped)
                    i += 2
                    if i < length and pattern[i] == '{' and self.readRegExpBracedQuantifierSyntax(pattern, i) is None:
                        output.append('\\{')
                        i += 1
                    continue

                if escaped in 'dDsSwWbBfnrtv0^$\\.*+?()[]{}|':
                    output.append(pattern[i:i + 2])
                elif escaped == '/':
                    output.append('/')
                else:
                    output.append(re.escape(escaped))
                i += 2
                continue

            if ch == '{':
                end = self.readRegExpBracedQuantifierSyntax(pattern, i)
                if end is None:
                    output.append('\\{')
                    i += 1
                else:
                    output.append(pattern[i:end])
                    i = end
                continue

            output.append(ch)
            i += 1

        return ''.join(output)

    def readUnicodeSetNestedClass(self, content, index):
        i = index + 1
        depth = 1
        nested = []
        length = len(content)

        while i < length and depth > 0:
            ch = content[i]
            if ch == '\\':
                if i + 2 < length and content[i + 1] in ('p', 'P', 'q') and content[i + 2] == '{':
                    end = self.skipRegExpBracedEscape(content, i)
                    nested.append(content[i:end])
                    i = end
                else:
                    nested.append(content[i:i + 2])
                    i += 2
            elif ch == '[':
                depth += 1
                nested.append(ch)
                i += 1
            elif ch == ']':
                depth -= 1
                if depth > 0:
                    nested.append(ch)
                i += 1
            else:
                nested.append(ch)
                i += 1

        if depth > 0:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return length, ''.join(nested)

        return i, ''.join(nested)

    def scanClassStringEscape(self, content, index):
        length = len(content)
        if index + 1 >= length:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return index + 1, 0

        escaped = content[index + 1]
        if escaped in 'bfnrtv':
            return index + 2, 1

        if escaped == '0':
            if index + 2 < length and Character.isDecimalDigit(content[index + 2]):
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return index + 2, 1

        if escaped == 'c':
            if index + 2 < length and content[index + 2] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
                return index + 3, 1
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return index + 2, 0

        if escaped == 'x':
            if index + 3 < length and Character.isHexDigit(content[index + 2]) and Character.isHexDigit(content[index + 3]):
                return index + 4, 1
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return min(index + 2, length), 0

        if escaped == 'u':
            if index + 2 < length and content[index + 2] == '{':
                i = index + 3
                start = i
                while i < length and content[i] != '}':
                    if not Character.isHexDigit(content[i]):
                        self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                        return i + 1, 0
                    i += 1
                if i == start or i >= length or int(content[start:i], 16) > 0x10FFFF:
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                    return i + 1, 0
                return i + 1, 1

            if index + 5 < length:
                digits = content[index + 2:index + 6]
                if all(Character.isHexDigit(ch) for ch in digits):
                    return index + 6, 1

            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return min(index + 2, length), 0

        escapable = set('^$\\.*+?()[]{}|/-')
        for punctuator in REGEXP_CLASS_SET_RESERVED_DOUBLE_PUNCTUATORS:
            escapable.update(punctuator)

        if escaped in escapable:
            return index + 2, 1

        self.tolerateUnexpectedToken(Messages.InvalidRegExp)
        return index + 2, 0

    def classStringDisjunctionMayContainStrings(self, content):
        i = 0
        length = len(content)
        count = 0
        mayContainStrings = False

        while i < length:
            ch = content[i]

            if ch == '|':
                if count != 1:
                    mayContainStrings = True
                count = 0
                i += 1
                continue

            if i + 1 < length and content[i:i + 2] in REGEXP_CLASS_SET_RESERVED_DOUBLE_PUNCTUATORS:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return False

            if ch == '\\':
                i, increment = self.scanClassStringEscape(content, i)
                count += increment
                continue
            else:
                if ch in REGEXP_CLASS_SET_SYNTAX_CHARACTERS:
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                    return False
                i += 1

            count += 1

        return mayContainStrings or count != 1

    def scanUnicodeSetOperand(self, content, index):
        length = len(content)
        if index >= length:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return index, False, False

        if index + 1 < length and content[index:index + 2] in REGEXP_CLASS_SET_RESERVED_DOUBLE_PUNCTUATORS:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return index + 2, False, False

        ch = content[index]

        if ch == '\\':
            if index + 1 >= length:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return index + 1, False, False

            if index + 2 < length and content[index + 1] in ('p', 'P') and content[index + 2] == '{':
                end, mayContainStrings = self.validateRegExpUnicodePropertyEscape(content, index, True, True)
                return end, mayContainStrings, False

            if index + 2 < length and content[index + 1] == 'q' and content[index + 2] == '{':
                end = self.skipRegExpBracedEscape(content, index)
                body = content[index + 3:end - 1] if end <= length and content[end - 1:end] == '}' else ''
                return end, self.classStringDisjunctionMayContainStrings(body), False

            end, _ = self.scanRegExpUnicodeEscapeSequence(content, index, True, True)
            return end, False, content[index + 1] not in 'dDsSwW'

        if ch == '[':
            end, nested = self.readUnicodeSetNestedClass(content, index)
            mayContainStrings = self.validateUnicodeSetClassOperators(nested)
            return end, False if nested.startswith('^') else mayContainStrings, False

        if ch in REGEXP_CLASS_SET_SYNTAX_CHARACTERS:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return index + 1, False, False

        return index + 1, False, True

    def validateUnicodeSetClassOperators(self, content):
        negated = content.startswith('^')
        i = 1 if negated else 0
        length = len(content)
        expressionKind = None
        expectOperand = True
        operandCount = 0
        operandsMayContainStrings = []
        lastOperandCanRange = False
        lastOperandWasRange = False

        while i < length:
            ch = content[i]

            if i + 1 < length and content[i:i + 2] in ('--', '&&'):
                current = content[i:i + 2]
                if expectOperand or expressionKind == 'union' or lastOperandWasRange:
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                    return False
                if expressionKind is None:
                    if operandCount != 1:
                        self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                        return False
                    expressionKind = current
                elif expressionKind != current:
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                    return False
                expectOperand = True
                lastOperandCanRange = False
                lastOperandWasRange = False
                i += 2
                continue

            if i + 1 < length and content[i:i + 2] in REGEXP_CLASS_SET_RESERVED_DOUBLE_PUNCTUATORS:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return False

            if expectOperand and expressionKind == '&&' and ch == '&':
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                return False

            if ch == '-':
                if expressionKind in ('--', '&&') or not lastOperandCanRange:
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                    return False
                end, mayContainStrings, canRange = self.scanUnicodeSetOperand(content, i + 1)
                if mayContainStrings or not canRange:
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                    return False
                operandsMayContainStrings[-1] = False
                expectOperand = False
                lastOperandCanRange = False
                lastOperandWasRange = True
                i = end
                continue

            if not expectOperand:
                if expressionKind in ('--', '&&'):
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                    return False
                expressionKind = 'union'

            end, mayContainStrings, canRange = self.scanUnicodeSetOperand(content, i)
            operandCount += 1
            operandsMayContainStrings.append(mayContainStrings)
            expectOperand = False
            lastOperandCanRange = canRange
            lastOperandWasRange = False
            i = end

        if expressionKind in ('--', '&&') and expectOperand:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return False

        if expressionKind == '&&':
            mayContainStrings = bool(operandsMayContainStrings) and all(operandsMayContainStrings)
        elif expressionKind == '--':
            mayContainStrings = operandsMayContainStrings[0] if operandsMayContainStrings else False
        else:
            mayContainStrings = any(operandsMayContainStrings)

        if negated and mayContainStrings:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return False

        return False if negated else mayContainStrings

    def sanitizeUnicodeSetClass(self, content):
        self.validateUnicodeSetClassOperators(content)

        if content == '^':
            return '\\s\\S'

        output = []
        i = 0
        length = len(content)

        while i < length:
            ch = content[i]

            if ch == '\\':
                if i + 2 < length and content[i + 1] in ('p', 'P') and content[i + 2] == '{':
                    self.validateRegExpUnicodePropertyEscape(content, i, True)
                    output.append('a')
                    i = self.skipRegExpBracedEscape(content, i)
                elif i + 2 < length and content[i + 1] == 'q' and content[i + 2] == '{':
                    output.append('a')
                    i = self.skipRegExpBracedEscape(content, i)
                else:
                    end, replacement = self.scanRegExpUnicodeEscapeSequence(content, i, True, True)
                    output.append(replacement)
                    i = end
                continue

            if i + 1 < length and content[i:i + 2] in ('--', '&&'):
                i += 2
                continue

            if ch in '[]':
                i += 1
                continue

            output.append(ch)
            i += 1

        return ''.join(output) or 'a'

    def sanitizeUnicodeSetsPattern(self, pattern):
        output = []
        i = 0
        length = len(pattern)

        while i < length:
            ch = pattern[i]

            if ch == '\\':
                if i + 2 < length and pattern[i + 1] in ('p', 'P') and pattern[i + 2] == '{':
                    self.validateRegExpUnicodePropertyEscape(pattern, i, True)
                    output.append('.')
                    i = self.skipRegExpBracedEscape(pattern, i)
                else:
                    end, replacement = self.scanRegExpUnicodeEscapeSequence(pattern, i, False, True)
                    output.append(replacement)
                    i = end
                continue

            if ch == '[':
                start = i
                i += 1
                depth = 1
                content = []
                while i < length and depth > 0:
                    ch = pattern[i]
                    if ch == '\\':
                        if i + 2 < length and pattern[i + 1] == 'q' and pattern[i + 2] == '{':
                            end = self.skipRegExpBracedEscape(pattern, i)
                            content.append(pattern[i:end])
                            i = end
                        else:
                            content.append(pattern[i:i + 2])
                            i += 2
                    elif ch == '[':
                        depth += 1
                        content.append(ch)
                        i += 1
                    elif ch == ']':
                        depth -= 1
                        if depth > 0:
                            content.append(ch)
                        i += 1
                    else:
                        content.append(ch)
                        i += 1

                if depth > 0:
                    self.tolerateUnexpectedToken(Messages.InvalidRegExp)
                    output.append(pattern[start:])
                    break

                output.append('[' + self.sanitizeUnicodeSetClass(''.join(content)) + ']')
                continue

            if ch == '{':
                end = self.validateRegExpBracedQuantifier(pattern, i)
                output.append(pattern[i:end])
                i = end
                continue

            if ch in ']}':
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)

            output.append(ch)
            i += 1

        return ''.join(output)

    def testRegExp(self, pattern, flags):
        self.validateRegExpFlags(flags)

        # The BMP character to use as a replacement for astral symbols when
        # translating an ES6 "u"-flagged pattern to an ES5-compatible
        # approximation.
        # Note: replacing with '\uFFFF' enables false positives in unlikely
        # scenarios. For example, `[\u{1044f}-\u{10440}]` is an invalid
        # pattern that would not be detected by this substitution.
        astralSubstitute = '\uFFFF'

        # Replace every Unicode escape sequence with the equivalent
        # BMP character or a constant ASCII code point in the case of
        # astral symbols. (See the above note on `astralSubstitute`
        # for more information.)
        def astralSub(m):
            codePoint = int(m.group(1) or m.group(2), 16)
            if codePoint > 0x10FFFF:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            elif codePoint <= 0xFFFF:
                ch = chr(codePoint)
                if ch in REGEXP_IDENTITY_ESCAPE_CHARACTERS:
                    return re.escape(ch)
                return ch
            return astralSubstitute

        pyflags = 0
        if 'm' in flags:
            pyflags |= re.M
        if 'i' in flags:
            pyflags |= re.I
        if 's' in flags:
            pyflags |= re.S

        # Python's regexp engine does not support UnicodeSets (`v`) syntax, so
        # compile a sanitized pattern to keep basic validation active.
        if 'v' in flags:
            captureCount = self.countRegExpCapturingGroups(pattern)
            self.validateRegExpQuantifierSuffixes(pattern)
            pattern = self.prepareRegExpPattern(pattern)
            self.validateRegExpAssertionQuantifiers(pattern)
            self.validateRegExpBracedQuantifiers(pattern)
            pattern = self.sanitizeRegExpLookbehindAssertions(pattern)
            pattern = self.sanitizeRegExpNumericBackreferences(pattern, captureCount)
            try:
                re.compile(self.sanitizeUnicodeSetsPattern(pattern), pyflags)
            except Exception:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return None

        if 'u' in flags:
            captureCount = self.countRegExpCapturingGroups(pattern)
            self.validateRegExpQuantifierSuffixes(pattern)
            self.validateRegExpAssertionQuantifiers(pattern)
            self.validateRegExpBracedQuantifiers(pattern)
            pattern = self.prepareRegExpPattern(pattern)
            pattern = self.sanitizeRegExpLookbehindAssertions(pattern)
            pattern = self.sanitizeRegExpNumericBackreferences(pattern, captureCount)
            pattern = self.sanitizeRegExpUnicodePattern(pattern)
            pattern = re.sub(r'[\uD800-\uDBFF][\uDC00-\uDFFF]', astralSubstitute, pattern)
            try:
                return re.compile(pattern, pyflags)
            except Exception:
                self.tolerateUnexpectedToken(Messages.InvalidRegExp)
            return None

        self.validateRegExpQuantifierSuffixes(pattern, False)
        self.validateLegacyRegExpLookbehindQuantifiers(pattern)

        pattern = self.prepareRegExpPattern(pattern, self.hasRegExpNamedCapturingGroup(pattern, False))
        pattern = re.sub(r'\\u([a-fA-F0-9]{4})', astralSub, pattern)

        # Replace each paired surrogate with a single ASCII symbol to
        # avoid throwing on regular expressions that are only valid in
        # combination with the "u" flag.
        pattern = re.sub(r'[\uD800-\uDBFF][\uDC00-\uDFFF]', astralSubstitute, pattern)

        pattern = self.sanitizeLegacyRegExpPattern(pattern)
        pattern = self.sanitizeLegacyRegExpLiteralBracesAfterQuantifiers(pattern)

        try:
            return re.compile(pattern, pyflags)
        except Exception:
            self.tolerateUnexpectedToken(Messages.InvalidRegExp)

    def scanRegExpBody(self):
        ch = self.source[self.index]
        assert ch == '/', 'Regular expression literal must start with a slash'

        str = self.source[self.index]
        self.index += 1
        classMarker = False
        terminated = False

        while not self.eof():
            ch = self.source[self.index]
            self.index += 1
            str += ch
            if ch == '\\':
                ch = self.source[self.index]
                self.index += 1
                # https://tc39.github.io/ecma262/#sec-literals-regular-expression-literals
                if Character.isLineTerminator(ch):
                    self.throwUnexpectedToken(Messages.UnterminatedRegExp)

                str += ch
            elif Character.isLineTerminator(ch):
                self.throwUnexpectedToken(Messages.UnterminatedRegExp)
            elif classMarker:
                if ch == ']':
                    classMarker = False

            else:
                if ch == '/':
                    terminated = True
                    break
                elif ch == '[':
                    classMarker = True

        if not terminated:
            self.throwUnexpectedToken(Messages.UnterminatedRegExp)

        # Exclude leading and trailing slash.
        return str[1:-1]

    def scanRegExpFlags(self):
        str = ''
        flags = ''
        while not self.eof():
            ch = self.source[self.index]
            if not Character.isIdentifierPart(ch):
                break

            self.index += 1
            if ch == '\\' and not self.eof():
                ch = self.source[self.index]
                if ch == 'u':
                    self.index += 1
                    restore = self.index
                    char = self.scanHexEscape('u')
                    if char:
                        flags += char
                        str += '\\u'
                        while restore < self.index:
                            str += self.source[restore]
                            restore += 1

                    else:
                        self.index = restore
                        flags += 'u'
                        str += '\\u'

                    self.tolerateUnexpectedToken()
                else:
                    str += '\\'
                    self.tolerateUnexpectedToken()

            else:
                flags += ch
                str += ch

        return flags

    def scanRegExp(self):
        start = self.index

        pattern = self.scanRegExpBody()
        flags = self.scanRegExpFlags()
        value = self.testRegExp(pattern, flags)

        return RawToken(
            type=Token.RegularExpression,
            value='',
            pattern=pattern,
            flags=flags,
            regex=value,
            lineNumber=self.lineNumber,
            lineStart=self.lineStart,
            start=start,
            end=self.index
        )

    def lex(self):
        if self.eof():
            return RawToken(
                type=Token.EOF,
                value='',
                lineNumber=self.lineNumber,
                lineStart=self.lineStart,
                start=self.index,
                end=self.index
            )

        ch = self.source[self.index]

        # ES2023: Hashbang grammar - only at the very beginning of source, always enabled
        if self.index == 0 and ch == '#' and self.index + 1 < self.length and self.source[self.index + 1] == '!':
            return self.scanHashbang()

        if Character.isIdentifierStart(ch):
            return self.scanIdentifier()

        # Very common: ( and ) and ;
        if ch in ('(', ')', ';'):
            return self.scanPunctuator()

        # String literal starts with single quote (U+0027) or double quote (U+0022).
        if ch in ('\'', '"'):
            return self.scanStringLiteral()

        # Dot (.) U+002E can also start a floating-point number, hence the need
        # to check the next character.
        if ch == '.':
            if Character.isDecimalDigit(self.source[self.index + 1]):
                return self.scanNumericLiteral()

            return self.scanPunctuator()

        if Character.isDecimalDigit(ch):
            return self.scanNumericLiteral()

        # Template literals start with ` (U+0060) for template head
        # or } (U+007D) for template middle or template tail.
        if ch == '`' or (ch == '}' and self.curlyStack and self.curlyStack[-1] == '${'):
            return self.scanTemplate()

        # ES2021: Private identifiers start with # - always enabled
        if ch == '#':
            return self.scanPrivateIdentifier()

        # Possible identifier start in a surrogate pair.
        cp = ord(ch)
        if cp >= 0xD800 and cp < 0xDFFF:
            cp = self.codePointAt(self.index)
            ch = Character.fromCodePoint(cp)
            if Character.isIdentifierStart(ch):
                return self.scanIdentifier()

        return self.scanPunctuator()
