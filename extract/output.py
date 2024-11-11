from pathlib import Path
from typing import NoReturn, TextIO
from .ast import *


def check_first_layer_is_all_Layer(ast: AST):
    assert all(isinstance(x, Layer) for x in ast.children)


def check_second_layer_is_all_Layer_or_Para(ast: AST):
    assert all(isinstance(y, (Layer, Para)) for x in ast.children for y in x.children)


def check_all_TextLike_are_under_Para_or_ListItem_or_Quote(ast: AST):
    def check(curr: AST, parent: AST | None) -> bool:
        if isinstance(curr, TextLike) and not isinstance(parent, (Para, ListItem, Quote)):
            return False
        return True

    assert all(pre_order_map(ast, check))


def error(ast: AST | None, *, prompt: str = "not implemented") -> NoReturn:
    raise RuntimeError(f"{prompt}: [{type(ast)}]: {ast}")


PREFIX = '''
#let character(it) = it
#let l_section(it) = it
#let p_normal(
	word_indent: "first-line", 
	para_indent: 0, 
	center: false,
	italic: false,
	bold: false,
	right: false,
	it
) = {
	it
}
#let p_quote = p_normal
#let p_poetry = p_normal
#let p_img = p_normal
#let p_title(it) = heading(level: 2, it)

#let l_ordered(it) = enum(it)
#let l_ordered_item(it) = enum.item(it)

#let l_unordered(it) = list(it)
#let l_unordered_item(it) = list.item(it)

#let t_footnote(target_label, this_label, it) = super([#link(target_label, it) #label(this_label)])
#let t_footnotecontent = t_footnote

#let t_img = image
'''

class OutputTypst:
    folder_path: Path
    curr_file: TextIO

    def __init__(self, folder_path: str):
        self._is_last_list_ordered = False
        self.folder_path = Path(folder_path)

    def output_book(self, ast: AST):
        check_first_layer_is_all_Layer(ast)
        check_second_layer_is_all_Layer_or_Para(ast)
        check_all_TextLike_are_under_Para_or_ListItem_or_Quote(ast)

        root_layer = ast
        self.curr_file = (self.folder_path / "main.typ").open('w')

        self.output_literal(PREFIX)
        self.output_literal('\n\n')
        for character_layer in root_layer.children:
            assert isinstance(character_layer, Layer)
            self.output_literal(f'#character[\n')
            self.output_Para(character_layer.title)
            self.output_children(character_layer)
            self.output_literal("]")
            if character_layer.ident:
                self.output_literal(f'<{character_layer.ident}>')
            self.output_literal("\n\n")

    def output_AST(self, ast: AST):
        if isinstance(ast, (TextLike, Quote, Img)):
            self.output_TextLike(ast)
        elif isinstance(ast, Para):
            self.output_Para(ast)
        elif isinstance(ast, (List, ListItem)):
            self.output_List(ast)
        elif isinstance(ast, Layer):
            self.output_Section(ast)
        else:
            error(ast)

    def output_children(self, ast: AST):
        for c in ast.children:
            self.output_AST(c)

    def output_literal(self, literal: str):
        self.curr_file.write(literal)

    def output_Section(self, ast: Layer):
        self.output_literal("#l_section[")
        self.output_children(ast)
        self.output_literal("]")

    def output_TextLike(self, ast: TextLike | Quote | Img):
        if isinstance(ast, Text):
            self.output_literal(ast.text)
        elif isinstance(ast, ItalicInline):
            self.output_literal("#emph[")
            self.output_literal(ast.text)
            self.output_literal("]")
        elif isinstance(ast, Quote):
            self.output_literal("#emph[")
            self.output_children(ast)
            self.output_literal("]")
        elif isinstance(ast, BoldInline):
            self.output_literal("#strong[")
            self.output_literal(ast.text)
            self.output_literal("]")
        elif isinstance(ast, SuperScript):
            self.output_literal("#super[")
            self.output_literal(ast.text)
            self.output_literal("]")
        elif isinstance(ast, FootNote):
            assert ast.ident
            self.output_literal(f"#t_footnote(<{ast.link_id}>, \"{ast.ident}\")[")
            self.output_literal(ast.text)
            self.output_literal("]")
        elif isinstance(ast, FootNoteContent):
            self.output_literal(f"#t_footnotecontent(<{ast.backlink_id}>, \"{ast.backlink_id.replace('nr', 'nt')}\")[")
            self.output_literal(ast.text)
            self.output_literal("]")
        elif isinstance(ast, Img):
            self.output_literal(f'#t_img("{ast.path.replace('../', './')}")')
        else:
            error(ast)

    def output_Para(self, ast: Para | Title):
        mapping = {
            Poetry: "p_poetry",
            QuotePara: "p_quote",
            ImgCaption: "p_img",
        }
        if ast.__class__ in mapping:
            self.output_literal(f"  #{mapping[ast.__class__]}[\n    ")
            self.output_children(ast)
            self.output_literal("\n  ]\n")
        elif isinstance(ast, Para):
            args = ""
            if ast.word_indent != 'first-line':
                args = f", word_indent: \"{ast.word_indent}\""
            if ast.para_indent != 0:
                args = f", para_indent: {ast.para_indent}"
            if ast.center:
                args = f", center: {'true' if ast.center else 'false'}"
            if ast.italic:
                args = f", italic: {'true' if ast.italic else 'false'}"
            if ast.bold:
                args = f", bold: {'true' if ast.bold else 'false'}"
            if ast.right:
                args = f", right: {'true' if ast.right else 'false'}"
            if args:
                args = f'({args[2:]})'

            self.output_literal(f"  #p_normal{args}[\n    ")
            self.output_children(ast)
            self.output_literal("\n  ]\n")
        elif isinstance(ast, Title):
            self.output_literal("  #p_title[\n    ")
            self.output_children(ast)
            self.output_literal("\n  ]\n")
        else:
            error(ast)

    def output_List(self, ast: List | ListItem):
        if isinstance(ast, List):
            self._is_last_list_ordered = ast.is_ordered
            func_name = "l_ordered" if ast.is_ordered else "l_unordered"
            self.output_literal(f"  #{func_name}[\n")
            self.output_children(ast)
            self.output_literal("]\n")

        elif isinstance(ast, ListItem):
            func_name = "l_ordered_item" if self._is_last_list_ordered else "l_unordered_item"
            self.output_literal(f"    #{func_name}[\n")
            self.output_children(ast)
            self.output_literal("]\n")
        else:
            error(ast)
