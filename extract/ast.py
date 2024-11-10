from dataclasses import KW_ONLY, dataclass, field
from typing import Iterable, Literal


@dataclass
class AST:
    _: KW_ONLY
    ident: str | None = None
    children: list["AST"] = field(default_factory=list)

    @property
    def is_leaf(self):
        return len(self.children) == 0

    def __iadd__[T: "AST"](self, children: Iterable[T]):
        self.children.extend(children)
        return self


@dataclass
class Layer(AST):
    """book, characters, sections, ..."""

    title: str | None = None


@dataclass
class TextLike(AST):
    text: str


class Text(TextLike):
    pass


class QuoteInline(TextLike):
    pass


class BoldInline(TextLike):
    pass


class ItalicInline(TextLike):
    pass


class SuperScript(TextLike):
    pass


@dataclass
class FootNote(TextLike):
    link: str

    @property
    def link_id(self) -> str:
        return self.link.split("#")[-1]


@dataclass
class FootNoteContent(TextLike):
    backlink: str

    @property
    def backlink_id(self) -> str:
        return self.backlink.split("#")[-1]


@dataclass
class Img(AST):
    path: str


@dataclass
class List(AST):
    is_ordered: bool


@dataclass
class ListItem(AST):
    pass


@dataclass
class Para(AST):
    _: KW_ONLY
    word_indent: Literal["first-line", "none", "non-first-line"] = "first-line"
    para_indent: int = 0
    center: bool = False
    italic: bool = False
    bold: bool = False
    right: bool = False


@dataclass
class Poetry(Para):
    word_indent = "none"
    para_indent: int = 1
    italic: bool = True


@dataclass
class QuotePara(Para):
    word_indent = "none"
    para_indent: int = 1
    italic: bool = True


@dataclass
class ImgCaption(Para):
    center: bool = True
    italic: bool = True


def print_ast(ast: AST, indent=0):
    def _print(*text, end="\n"):
        print(" " * (indent), *text, sep="", end=end)

    # General
    _print("", end="")
    print(ast.__class__.__name__, end="")
    if ast.ident:
        print(f" <{ast.ident}>", end="")
    print()

    # Args
    match ast:
        case Layer(title):
            _print("  > title:", title)
        case TextLike(text) as tl:
            if len(text) < 20:
                _print("  > text:", text.__repr__())
            else:
                _print("  > text (len):", len(text))
            if isinstance(tl, FootNote):
                _print("  > link:", tl.link)
            if isinstance(tl, FootNoteContent):
                _print("  > backlink:", tl.backlink)
        case Para() as p:
            # Print only if not default
            if p.word_indent != "first-line":
                _print("  > word_indent:", p.word_indent)
            if p.para_indent != 0:
                _print("  > para_indent:", p.para_indent)
            # Style
            _print("  > style:", end="")
            if p.center:
                print(" center", end="")
            if p.right:
                print(" right", end="")
            if p.italic:
                print(" italic", end="")
            if p.bold:
                print(" bold", end="")
            print()
        case Img(path):
            _print("  > path:", path)

    # Children
    for child in ast.children:
        print_ast(child, indent + 4)
