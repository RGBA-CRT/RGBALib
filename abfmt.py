#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
abfmt - ActiveBasic 4 formatter / simple linter (prototype, v0.6.2)

v0.6.2 (2026-11-15, full-repo run on sPlayer: 46 .bp files):
  * 'if c then : stmt' -- a one-line If whose body follows on the same
    line after a colon -- was counted as a block opener, shifting the
    rest of the file (WaveView2.sbp lines 351/396, balance +2). In
    block_delta_line, an 'if ... then' segment that is followed by
    another segment on the same line now opens nothing, and a matching
    same-line 'endif' is cancelled with it. An opener in last position
    ('stmt : if c then') still opens; 'else if' is untouched.

v0.6.1 (2026-11-15, from SoundEffectors.abp):
  * The two-word closer 'End If' (also written 'end<TAB>if') was not
    recognized -- only 'endif' was -- so every line after the first
    'End If' shifted one level deeper and the file ended at level +2.
    'if' joined the block nouns after 'End'. (Per KEYWORD_CASE it
    formats as 'End if': End is Title, if is lower.)

v0.6 (2026-11-15, from NezPulg.abp / SET_Main.sbp / SET_TAB1.sbp):
  * With ... End With / EndWith is a block: the body indents, and
    '.member' lines inside are just statements. ('with'/'endwith'
    added to KEYWORD_CASE.)
  * ' ab-format off' ... ' ab-format on' comment markers (clang-format
    style; SET_TAB1.sbp already contained them): lines in between are
    emitted VERBATIM in both modes, while block levels are still
    tracked so indentation after 'on' stays correct.
  * Member names after '.' / '->' are NEVER keyword-cased and a '('
    after them always attaches: '.alias' stays '.alias', and class
    member calls like obj.Open( / .Close( are no longer rewritten to
    'Open (' just because Open/Close are also statements.
  * '.' spacing is context-aware: it glues only after a value
    (obj.member, a[0].x); after a keyword/operator/comma it starts a
    With-member reference and takes a space: 'if .Channel = 0',
    'FALSE OR .x', 'Foo(a, .y)'. (Was: 'if.Channel', 'OR.x', ',.y'.)
    '[' likewise glues only after a value: 'x = [ ... ]' keeps its
    space. Block comments keep their original separation.
  * block_delta extracts WHOLE identifiers: 'loop_flag = "[LOOP]"'
    was misread as a Do-Loop closer (word split at '_') and collapsed
    the indentation of a whole nested-if region in NezPulg.abp.
    One-word 'Elseif' is now an else-branch (dedent+indent), and
    ExitFor/ExitDo joined KEYWORD_CASE.
  * ':' is a statement separator (= newline): block balance is now
    computed per colon-separated segment, so one-line definitions
    'Sub X() : stmt : End Sub' (SET_Main.sbp) net to zero instead of
    leaking +1 each. A space before ':' is kept when the author wrote
    one ('stmt : stmt'), dropped when not ('stmt: stmt').
  * Continuation lines get +1 in --indent mode in general (was:
    conditions only): long argument lists (wsprintf(...) _ / args...)
    and array literals indent one level. A continuation is a line
    after a trailing '_' OR inside unclosed '(' / '[' (NezPulg's
    wsprintf at 855 continues with no '_'); a continuation line that
    starts with ')' or ']' (the closer) stays at the base level.
  * A line consisting of '*Label' (a Goto label) gets NO indent in
    --indent mode, like preprocessor lines (user rule).

v0.5 (2026-11-15, from Dummy.sbp):
  * Preprocessor lines (#ifdef/#endif/#define...) get NO indent.
  * Class access sections: a lone Public/Private/Protected line sits at
    the Class level; 'Public Function ...' still opens a body block.
  * '_' continuations of a condition (if/while): continuation lines get
    +1, and a multi-line If opens its block on the line carrying 'then'
    ('if (a) _' / 'AND (b) then' / body / endif now indents correctly).
  * Dummy.sbp (381 lines) passes --check UNCHANGED in preserve mode.

v0.4 (2026-11-15, from ChMask.sbp):
  * NOT attaches to '(': NOT(a) -- but 'NOT a' keeps the space.
    ChMask's own 'NOT (x)' (7 places) is normalized to NOT(x).
  * Select indent: Case goes one level under Select Case, bodies one
    more under Case, End Select back to Select's level (a Select stack
    tracks whether a Case body is open).

v0.3 (2026-11-15, from About.sbp):
  * AND / OR / NOT / XOR are normalized to UPPER case (user decision).
  * 'if ... then _' trick: a one-line If whose body is the next logical
    line via '_' continuation (no endif). --indent now gives that body a
    one-shot +1 indent instead of flattening it; it is NOT counted as a
    block for --lint balance.

v0.2 lessons from a real file (sPlayer.abp, 1,289 lines, cp932/CRLF):
  * DEFAULT is conservative: original indentation is PRESERVED. The author
    indents top-level Dim/Const sections by hand, and lint.bat never
    re-indented either. Re-indentation is opt-in via --indent.
  * Whitespace runs containing a TAB are alignment, not spacing: they are
    preserved verbatim between tokens (trailing-comment alignment,
    'VTable->init<TAB>= ...', 'Const X<TAB>= ...').
  * Unary operators are real: '= -1', 'As *Function(...)', 'As *RECT',
    'Path As *FilePathW' must not become '- 1' / '* Function'.
  * One-word keywords exist alongside two-word ones: ExitFunction,
    ExitSub, SelectCase, EndSelect (file also uses 'End Enum', 'endif').

Design (see README.md):
  * Token-based, NOT sed/regex on raw text, NOT a full AST formatter yet.
    Strings, ' line comments and /* */ block comments are single tokens and
    their contents are never rewritten -- this replaces the ##SP## / ##EQ##
    placeholder hack in sPlayer's lint.bat + lint_string_backup.py.
  * Encoding: cp932 in/out, line endings always CRLF on write.
  * Formatting is idempotent: format(format(x)) == format(x). Tested on
    the sample and on sPlayer.abp itself.

Usage:
  python3 abfmt.py file.abp            # formatted result to stdout
  python3 abfmt.py -i file.abp ...     # rewrite in place
  python3 abfmt.py --check file.abp    # exit 1 if not formatted (CI/lint)
  python3 abfmt.py --lint file.abp     # block-balance etc. only
  python3 abfmt.py --indent file.abp   # also re-indent by block level (TAB)
"""
import argparse, re, sys
from dataclasses import dataclass

# ---------------------------------------------------------------- keywords
# Canonical case. sPlayer lint.bat evidence is kept where it exists:
#   Sub / Function / End Sub / End Function / Dim / As / DWord -> Title-ish
#   if / then / else / endif / sizeof / #ifdef                -> lower
# One-word forms observed in real code are included. Edit this table --
# it is also the single source for the VSCode TextMate grammar.
KEYWORD_CASE = {
    "sub": "Sub", "function": "Function", "dim": "Dim", "as": "As",
    "if": "If", "then": "Then", "else": "Else", "endif": "EndIf",
    "sizeof": "sizeof",
    "end": "End", "exit": "Exit", "for": "For", "to": "To", "step": "Step",
    "next": "Next", "while": "While", "wend": "Wend", "do": "Do",
    "loop": "Loop", "select": "Select", "case": "Case", "return": "Return",
    "goto": "Goto", "continue": "Continue",
    # one-word forms (real code, 2026-11-15 sPlayer.abp)
    "exitsub": "ExitSub", "exitfunction": "ExitFunction",
    "exitfor": "ExitFor", "exitdo": "ExitDo",
    "selectcase": "SelectCase", "endselect": "EndSelect",
    "with": "With", "endwith": "EndWith", "elseif": "ElseIf",
    "endtype": "EndType", "endclass": "EndClass", "endenum": "EndEnum",
    "endsub": "EndSub", "endfunction": "EndFunction",
    "addressof": "AddressOf", "varptr": "VarPtr",
    "class": "Class", "inherits": "Inherits", "type": "Type",
    "enum": "Enum", "const": "Const", "declare": "Declare", "lib": "Lib",
    "alias": "Alias", "export": "Export", "virtual": "Virtual",
    "typedef": "TypeDef", "byval": "ByVal", "byref": "ByRef",
    "private": "Private", "protected": "Protected", "public": "Public",
    "new": "New", "delete": "Delete", "and": "AND", "or": "OR",
    "xor": "XOR", "not": "NOT", "mod": "Mod",
    "print": "Print", "input": "Input", "open": "Open", "close": "Close",
    "debug": "Debug",
    "byte": "Byte", "word": "Word", "dword": "DWord", "long": "Long",
    "integer": "Integer", "single": "Single", "double": "Double",
    "string": "String", "boolean": "Boolean", "void": "Void",
    "qword": "QWord", "int64": "Int64",
}
# keywords that behave like function calls for '(' spacing: Foo(, sizeof(
CALLABLE_KEYWORDS = {"sizeof", "addressof", "varptr"}

# ---------------------------------------------------------------- lexer
@dataclass
class Tok:
    kind: str
    text: str

TOKEN_RE = re.compile(r"""
    (?P<block_comment>/\*.*?\*/) |
    (?P<line_comment>'[^\r\n]*) |
    (?P<string>(?:[Ee][Xx])?"(?:[^"\r\n]|"")*") |
    (?P<ident>\d+[A-Za-z_][A-Za-z0-9_]*|[~]?[A-Za-z_][A-Za-z0-9_]*\$?|\#[A-Za-z]+) |
    (?P<number>&[Hh][0-9A-Fa-f]+|&[Oo][0-7]+|\d+(?:\.\d+)?) |
    (?P<op><<=|>>=|\+=|-=|\*=|/=|\\=|\+\+|--|->|<=|>=|=<|=>|<>|><|<<|>>|[-+*/\\=<>&]) |
    (?P<punct>[(),.\[\]:;]) |
    (?P<ws>[ \t]+) |
    (?P<other>.)
""", re.VERBOSE | re.DOTALL)

def lex_line(line: str):
    toks, i = [], 0
    while i < len(line):
        m = TOKEN_RE.match(line, i)
        if not m:
            toks.append(Tok("other", line[i])); i += 1; continue
        toks.append(Tok(m.lastgroup, m.group())); i = m.end()
    return toks

# ---------------------------------------------------------------- spacing
VALUE_KINDS = {"ident", "number", "string"}
BINARY_OPS = {"=", "+", "-", "*", "/", "\\", "<", ">", "<=", ">=",
              "=<", "=>", "<>", "><", "<<", ">>", "+=", "-=", "*=",
              "/=", r"\=", "<<=", ">>=", "&"}

def is_value(tok):
    if tok is None:
        return False
    if tok.kind in ("number", "string"):
        return True
    if tok.kind == "ident":
        # keywords (As, Then, Return...) are not values: 'As *Type',
        # 'Return -1' have a unary operator after them
        return tok.text.lower() not in KEYWORD_CASE
    return tok.text in (")", "]", "++", "--")

def format_tokens(toks):
    """Rebuild one line (indent already stripped) with canonical spacing.
    String/comment contents verbatim; TAB-containing gaps verbatim."""
    out, prev, pending_ws = [], None, ""
    prev_unary = False
    prev_member = False  # prev token was a member name (after '.'/'->')
    ptr_type = False   # just saw '*Function' / '*Sub': '(' attaches directly
    for t in toks:
        if t.kind == "ws":
            pending_ws = t.text; continue
        text = t.text
        # an identifier right after '.' or '->' is a MEMBER name: it is
        # never keyword-cased ('.alias' is a field, obj.Open( is a method
        # call -- Open/Close/Print are also statements, v0.6)
        member = prev is not None and prev.text in (".", "->")
        if t.kind == "ident":
            low = text.lstrip("#").lower()
            if text.startswith("#"):
                text = "#" + low
            elif low in KEYWORD_CASE and not member:
                text = KEYWORD_CASE[low] + ("$" if text.endswith("$") else "")
        cur = Tok(t.kind, text)
        # a member name behaves like a value (callable, indexable...)
        prev_value = is_value(prev) or prev_member
        # classify operator arity by what precedes it
        unary = False
        if text in ("+", "-", "*"):
            unary = not prev_value
        elif text in ("++", "--"):
            unary = not prev_value         # postfix if a value precedes
        # --- space before this token?
        space = False; keep_tab_gap = False
        if prev is not None:
            p, c = prev.text, text
            if c in (")", "]", ","):
                space = False
            elif p in ("(", "["):
                space = False
            elif prev_unary:
                space = False               # '-1', '*Function', '++x'
            elif cur.kind == "block_comment" or prev.kind == "block_comment":
                space = bool(pending_ws)    # keep the author's separation
            elif c == "(" and p.upper() == "NOT":
                space = False               # unary NOT attaches: NOT(a),
                                            # but 'NOT a' keeps its space
            elif c == "(" and ptr_type:
                space = False               # '*Function(' pointer type
            elif c == "(" and prev.text in (")", "]"):
                space = False               # 'GetActiveWnd()(exclude...)' quirk
            elif c == "(" and (prev_member or
                               (prev.kind == "ident" and
                                (prev.text.lower() not in KEYWORD_CASE
                                 or prev.text.lower() in CALLABLE_KEYWORDS))):
                space = False               # call: Foo( / sizeof( / obj.Open(
            elif c == "(":
                space = True                # keyword + '(': 'if (', 'And ('
            elif c == "[":
                space = not prev_value      # index glues: a[0]; but the
                                            # array literal in 'x = [ 1 ]'
                                            # keeps the space after '='
            elif p in (".", "->"):
                space = False               # member name glues to its dot
            elif c in (".", "->"):
                # glues after a value (obj.member); after a keyword,
                # operator or comma it STARTS a With-member reference:
                # 'if .x', 'a OR .y', 'Foo(a, .z)' all take a space (v0.6)
                space = not prev_value
            elif c in ("++", "--") and prev_value:
                space = False               # postfix: x++
            elif c in BINARY_OPS or p in BINARY_OPS:
                space = True
            elif c == ";":
                space = False
            elif c == ":":
                # ':' is a statement separator: keep ONE space when the
                # author wrote whitespace before it ('stmt : stmt'),
                # none when not ('stmt: stmt'); TAB gaps stay verbatim
                space = bool(pending_ws)
            elif p in (";", ":"):
                space = True
            elif p == ",":
                space = True
            elif is_value(prev) or prev.kind in ("line_comment",) or \
                    cur.kind in VALUE_KINDS or cur.kind == "line_comment":
                space = True
            # a TAB in the original gap means deliberate alignment:
            # preserve it verbatim (except after '(' / '[' and before
            # ')' / ']', where it can only be noise)
            if "\t" in pending_ws and c not in (")", "]") \
                    and p not in ("(", "[") \
                    and not (c == "(" and p.upper() == "NOT"):
                keep_tab_gap = True
        if out:
            if keep_tab_gap:
                out.append(pending_ws)
            elif space:
                out.append(" ")
        out.append(text)
        ptr_type = bool(prev_unary and prev is not None and prev.text == "*"
                        and text.lower() in ("function", "sub")) \
            if t.kind == "ident" else (ptr_type and text == "(")
        prev, prev_unary, pending_ws = cur, unary, ""
        prev_member = member and t.kind == "ident"
    return "".join(out).rstrip()

# ---------------------------------------------------------------- blocks
def block_delta(s: str):
    """(dedent_before, indent_after) for ONE statement -- used only by
    --indent / --lint. Colon-separated lines go through
    block_delta_line(), which calls this per segment."""
    # WHOLE identifiers: splitting at '_' made 'loop_flag = "[LOOP]"'
    # look like a Do-Loop closer (NezPulg.abp, v0.6)
    w = re.findall(r"[A-Za-z#][A-Za-z0-9_]*", s.lower())
    if not w:
        return 0, 0
    code = s.split("'")[0].lower()
    low = s.lower().strip()
    dedent = indent = 0
    # bare 'End' is the halt statement, NOT a block closer (real code:
    # top-level main loop ends with plain 'End'); 'End' closes only when
    # followed by a block noun. One-word EndXxx forms also close.
    if (w[0] == "end" and len(w) > 1
            and w[1] in ("sub", "function", "class", "type", "enum",
                         "select", "with", "if")) \
            or w[0] in ("next", "wend", "loop") \
            or w[0] in ("endif", "endselect", "endtype", "endclass",
                        "endenum", "endsub", "endfunction", "endwith"):
        dedent = 1
    elif w[0] in ("else", "case", "elseif"):
        dedent = 1; indent = 1
    # access modifiers may prefix a definition: 'Public Function Foo()'
    # has a body, but 'Virtual/Export Function ...' is only a declaration
    low_core = low
    while re.match(r"(public|private|protected)\s+", low_core):
        low_core = re.sub(r"^(public|private|protected)\s+", "", low_core)
    if re.match(r"(sub|function|class|type|enum)\b", low_core) \
            and not low.startswith(("end", "declare")) \
            and not low_core.startswith(("virtual", "export")) \
            and "=" not in low:
        indent = 1
    elif re.match(r"selectcase\b", low) or re.match(r"select\s+case\b", low):
        # NOT 'SelectRecode = FALSE' (assignment to a Function's name)
        indent = 1
    elif w[0] in ("for", "while"):
        indent = 1
    elif w[0] == "with":
        indent = 1
    elif w[0] == "do" and (low == "do" or low.startswith("do ")):
        indent = 1
    elif w[0] == "if" and re.search(r"\bthen\s*$", code):
        indent = 1
    return dedent, indent

def block_delta_line(toks):
    """(dedent_before, indent_after) for a whole physical line. ':' is
    a statement separator with the same meaning as a newline, so the
    line is split into segments at depth-0 colons and each segment's
    delta is combined: 'Sub X() : stmt : End Sub' nets to (0, 0),
    'stmt : endif' dedents for the NEXT line without dedenting this
    one. Colons inside parens/brackets, strings and comments are not
    separators."""
    segs, cur, depth = [], [], 0
    for t in toks:
        if t.kind == "line_comment":
            break
        if t.kind in ("ws", "block_comment"):
            continue
        if t.kind == "punct" and t.text == ":" and depth == 0:
            segs.append(cur); cur = []; continue
        if t.kind == "punct":
            if t.text in ("(", "["):
                depth += 1
            elif t.text in (")", "]"):
                depth -= 1
        cur.append(t)
    segs.append(cur)
    nonempty = [seg for seg in segs if seg]
    dedent_before, net, seen = 0, 0, False
    cancelled_ifs = 0  # one-line Ifs opened AND closed on this line
    for idx, seg in enumerate(nonempty):
        text = " ".join(t.text for t in seg)
        d, i = block_delta(text)
        words = [t.text.lower() for t in seg if t.kind == "ident"]
        # 'if c then : stmt' -- the body follows on the SAME line after
        # a colon, so this If is a one-liner and opens no block (its
        # 'endif', if one is written on the same line, is cancelled
        # too). An opener in LAST position keeps its indent: the body
        # is on the following lines. 'else if' is not cancelled: its
        # dedent/indent pair belongs to the enclosing If.
        if words[:1] == ["if"] and i > 0 and idx < len(nonempty) - 1:
            i = 0
            cancelled_ifs += 1
        elif cancelled_ifs and (words[:1] == ["endif"]
                                or words[:2] == ["end", "if"]):
            d = 0
            cancelled_ifs -= 1
        if not seen:
            dedent_before, seen = d, True
        net += i - d
    return dedent_before, dedent_before + net

def paren_depth(toks):
    """Net '(' + '[' minus ')' + ']' over the code tokens of a line
    (strings/comments are single tokens, so their parens never count).
    > 0 at end of line means the logical line continues on the next
    physical line even without a trailing '_'."""
    depth = 0
    for t in toks:
        if t.kind == "punct":
            if t.text in ("(", "["):
                depth += 1
            elif t.text in (")", "]"):
                depth -= 1
    return depth

# ' ab-format off' / ' ab-format on' (also /* ... */ form): clang-format
# style markers, v0.6. Lines between off and on are emitted verbatim.
FMT_MARKER_RE = re.compile(r"^(?:'\s*|/\*\s*)ab-format\s+(off|on)\b", re.I)
# a Goto label line: '*Name' alone (optionally '*Name:' / trailing comment)
LABEL_RE = re.compile(r"^\*[A-Za-z_~][A-Za-z0-9_]*\s*(:\s*)?('.*)?$")

def format_text(text: str, reindent: bool = False):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    out, level, in_block = [], 0, False
    temp = 0   # one-shot indent depth from 'if ... then _' bodies (below)
    select_stack = []  # per open Select: True once a Case body is open.
    in_cont = False    # this physical line continues the previous one
    depth = 0          # unclosed '(' / '[' depth of the logical line
    logical_start = [] # first meaningful tokens of the current logical line
    pending_indent = 0 # block-open deferred until a logical line completes
    fmt_off = False    # between ' ab-format off' and ' ab-format on'
    # Select style (user, 2026-11-15): Case indents under Select, the
    # body indents under Case, End Select returns to Select's level:
    #   Select Case x / <TAB>Case 1 / <TAB><TAB>body / End Select
    for raw in text.split("\n"):
        if in_block:
            # inside /* */ : verbatim (raw in an ab-format off region)
            out.append(raw if fmt_off else raw.rstrip())
            if "*/" in raw: in_block = False
            continue
        stripped = raw.strip()
        marker = FMT_MARKER_RE.match(stripped)
        if marker:
            fmt_off = marker.group(1).lower() == "off"
            out.append(raw[:len(raw) - len(raw.lstrip(" \t"))] + stripped)
            continue
        if not stripped:
            out.append(raw if fmt_off else ""); continue
        leading = raw[:len(raw) - len(raw.lstrip(" \t"))]
        if stripped.startswith("#"):
            # preprocessor (#ifdef/#endif/#define...): NO indent in
            # --indent mode (user, 2026-11-15), like C's preprocessor
            out.append(raw if fmt_off else
                       (("" if reindent else leading) + stripped))
            continue
        if stripped.startswith("/*"):
            # comment-only line: NEVER re-indent, even with --indent
            # (user, 2026-11-15) -- commented-out code keeps its own
            # indentation, which often differs from the live block level
            out.append(raw if fmt_off else leading + stripped)
            if "*/" not in stripped[2:]: in_block = True
            continue
        toks = lex_line(raw.lstrip(" \t"))
        formatted = format_tokens(toks)
        if toks and toks[0].kind == "line_comment":
            # comment-only line: original indentation is preserved even
            # in --indent mode; also does not consume a pending
            # one-shot if body
            out.append(raw if fmt_off else leading + formatted)
            continue
        # --- logical lines and continuation. A logical line continues
        # on the next physical line when it ends with '_' OR when a
        # '(' / '[' is still unclosed (long argument lists such as
        # wsprintf(...) break without '_', v0.6). Continuation lines
        # get +1 in --indent mode, except one that starts with the
        # closer ')' / ']' itself. A condition may be broken mid-way
        # ('if (a) _' / 'AND (b) then'): the block only opens when the
        # line carrying 'then' completes. Also the 'if ... then _'
        # trick: a one-line If whose body is the NEXT logical line (no
        # endif), so it must NOT become a permanent block level (lint
        # balance!) -- it is a one-shot indent for one logical statement.
        meaningful = [t.text.lower() for t in toks
                      if t.kind not in ("ws", "line_comment", "block_comment")]
        if not in_cont:
            logical_start = meaningful[:2]
        logical_is_if = logical_start[:1] == ["if"] \
            or logical_start[:1] == ["elseif"] \
            or logical_start[:2] == ["else", "if"]
        cont_extra = 1 if (in_cont and meaningful
                           and meaningful[0] not in (")", "]")) else 0
        ends_cont = bool(meaningful) and meaningful[-1] == "_"
        depth += paren_depth(toks)
        line_open = ends_cont or depth > 0
        is_if_cont = ends_cont and len(meaningful) >= 2 \
            and meaningful[-2] == "then" and logical_is_if
        dedent, indent = block_delta_line(toks)
        if is_if_cont:
            dedent = 1 if logical_start[:1] == ["else"] else 0
            indent = 0
        elif line_open and indent > 0:
            pending_indent = indent  # opener lands on the completing line
            indent = 0
        if not line_open:
            if pending_indent and indent == 0:
                indent = pending_indent
            pending_indent = 0
            if in_cont and logical_is_if and indent == 0 \
                    and formatted.split("'")[0].rstrip().lower().endswith("then"):
                indent = 1           # 'then' arrived on a continuation line
        # access-modifier section line in a Class ('Public' alone):
        # sits at the Class level itself, members after it re-indent
        if meaningful in (["public"], ["private"], ["protected"],
                          ["public", ":"], ["private", ":"],
                          ["protected", ":"]) and level > 0:
            dedent, indent = 1, 1
        # --- Select / Case / End Select (see select_stack note above)
        is_select_open = bool(meaningful) and (
            meaningful[0] == "selectcase"
            or meaningful[:2] == ["select", "case"])
        is_case = bool(meaningful) and meaningful[0] == "case"
        is_endselect = bool(meaningful) and (
            meaningful[0] == "endselect"
            or meaningful[:2] == ["end", "select"])
        if is_case and select_stack:
            dedent = 1 if select_stack[-1] else 0
            indent = 1
        elif is_endselect and select_stack:
            dedent = 2 if select_stack[-1] else 1
            indent = 0
        base = max(0, level - dedent)
        if fmt_off:
            out.append(raw)          # ab-format off region: verbatim,
                                     # but the state above still tracked
        elif reindent:
            # a '*Label' Goto label line gets NO indent (user, v0.6),
            # like a preprocessor line
            tabs = 0 if LABEL_RE.match(stripped) \
                else base + temp + cont_extra
            out.append(("\t" * tabs + formatted) if formatted else "")
        else:
            out.append((leading + formatted) if formatted else "")
        level = base + indent
        # --- advance the Select stack
        if is_endselect and select_stack:
            select_stack.pop()
        elif is_select_open:
            select_stack.append(False)
        elif is_case and select_stack:
            select_stack[-1] = True
        # --- advance the one-shot state
        if is_if_cont:
            temp += 1            # next logical line is the body (+ nesting)
        elif line_open:
            pass                 # same logical line continues; body pending
        elif indent > 0 and temp > 0:
            pass                 # body opened a block; it ends at its closer
        else:
            temp = 0             # one logical statement done: one-shots end
        # --- advance the continuation state
        in_cont = bool(line_open and not is_if_cont)
        if depth < 0:
            depth = 0            # a stray closer must not poison the file
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n", level

def lint_text(text: str):
    problems = []
    _, level = format_text(text)
    if level != 0:
        problems.append(f"block balance: level {level} at EOF "
                        f"(unclosed or over-closed block?)")
    if "\r\n" not in text and "\n" in text:
        problems.append("line endings: LF found (ActiveBasic expects CRLF)")
    for i, line in enumerate(text.splitlines(), 1):
        if line != line.rstrip():
            problems.append(f"{i}: trailing whitespace")
    return problems

# ---------------------------------------------------------------- io / cli
def read_input(path):
    if path == "-":
        return sys.stdin.buffer.read().decode("cp932")
    with open(path, "rb") as f:
        return f.read().decode("cp932")

def main(argv=None):
    ap = argparse.ArgumentParser(prog="abfmt")
    ap.add_argument("files", nargs="+")
    ap.add_argument("-i", "--in-place", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--lint", action="store_true")
    ap.add_argument("--indent", action="store_true",
                    help="re-indent by block level (default: preserve)")
    a = ap.parse_args(argv)
    rc = 0
    for path in a.files:
        src = read_input(path)
        if a.lint:
            for p in lint_text(src):
                print(f"{path}: {p}"); rc = 1
            continue
        formatted, _ = format_text(src, reindent=a.indent)
        if a.check:
            if src.replace("\r\n", "\n") != formatted:
                print(f"{path}: not formatted"); rc = 1
        elif a.in_place and path != "-":
            with open(path, "wb") as f:
                f.write(formatted.replace("\n", "\r\n").encode("cp932"))
        else:
            sys.stdout.buffer.write(
                formatted.replace("\n", "\r\n").encode("cp932"))
    return rc

if __name__ == "__main__":
    raise SystemExit(main())
