from typing import Iterable, NoReturn
import sys
from ebooklib import epub
import ebooklib

import bs4
from bs4 import BeautifulSoup

from .ast import *


def error(elm: bs4.PageElement | None, *, prompt: str = "not implemented") -> NoReturn:
    raise RuntimeError(f"{prompt}: [{type(elm)}]: {elm}")


def assert_one_child(tag: bs4.Tag) -> bs4.PageElement:
    if len(list(tag.children)) != 1:
        error(tag, prompt="expect one child")
    return tag.children.__iter__().__next__()


def assert_tag(elm: bs4.PageElement | None, name: str) -> bs4.Tag:
    if not isinstance(elm, bs4.Tag) or elm.name != name:
        error(elm, prompt=f"expect <{name}>")
    return elm


def assert_attr(tag: bs4.Tag, attr_name: str) -> str:
    if attr_name not in tag.attrs:
        error(tag, prompt=f"expect attr '{attr_name}'")
    return tag.attrs[attr_name]


def para_inside(para_elm: bs4.Tag) -> Iterable[AST]:

    def translate_tag(tag: bs4.Tag) -> AST | None:
        klass = tag.attrs.get("class")
        match tag.name:
            case "span" if klass == "dropcaps":
                return Text(tag.text)
            case "em" if klass == "calibre4":
                return QuoteInline(tag.text)
            case "em" if klass == "calibre8":
                return Text(tag.text)
            case "sup" if klass in ["calibre9", "calibre17", "calibre18"]:
                children = list(tag.children)
                if len(children) == 2:
                    first_a = assert_tag(children[0], "a")
                    second_a = assert_tag(children[1], "a")
                    ident = assert_attr(first_a, "id")
                    href = assert_attr(second_a, "href")
                    return FootNote(ident=ident, link=href, text=tag.text)
                elif len(children) == 1:
                    return SuperScript(tag.text)
                else:
                    error(tag)
            case "a":
                elm = assert_tag(assert_one_child(tag), "b")
                assert assert_attr(elm, "class") == "calibre7"
                return FootNoteContent(backlink=assert_attr(tag, "href"), text=tag.text)
            case "small" if klass in ["calibre5", "calibre11"]:
                return Text(tag.text)
            case "img" if klass == "calibre2":
                path = assert_attr(tag, "src")
                return Img(path=path)
            case "b" if klass in ["calibre7", "calibre15"]:
                return BoldInline(tag.text)
            case "i" if klass == "calibre4":
                return ItalicInline(tag.text)
            case "br" if klass == "calibre1":
                return Text("\n")
        return None

    for c in para_elm.children:
        if isinstance(c, bs4.NavigableString):
            yield Text(c)
        elif isinstance(c, bs4.Tag):
            child = translate_tag(c)
            if child is None:
                error(c)
            yield child


BIBLIOGRAPHY_ITEM = "text/part0221.html"
EXCLUDES = set(
    [
        # Need Manual Translate
        "titlepage.xhtml",
        "text/part0000.html",  # Front matter
        "text/part0002.html",  # ToC
        "text/part0006.html",  # 原书封面
        "text/part0011.html",  # Book 1 封面
        "text/part0086.html",  # Book 1 结尾
        "text/part0087.html",  # Book 2 开头
        "text/part0088.html",  # Book 2 开头
        "text/part0140.html",  # 有一张表格
        "text/part0150.html",  # Book 2 结尾
        "text/part0151.html",  # Book 3 开头
        "text/part0152.html",  # Book 3 开头
        "text/part0219.html",  # Book 3 结尾
        # Can ignore
        "text/part0222.html",  # About the author
        "text/part0223.html",  # About the press
        "text/part0224.html",  # Books of related interests
        "text/part0225_split_000.html",  # Back matter
        "text/part0225_split_001.html",
        "text/part0227.html",  # Back matter
        # Index
        *(f"text/part0226_split_{str(i).zfill(3)}.html" for i in range(0, 90 + 1)),
    ]
)
NON_UNIQUE_IDENT = set(["calibre_pb_0"])


def translate_list(list_elm: bs4.Tag) -> List:
    if list_elm.name == "ol":
        assert assert_attr(list_elm, "class") == "calibre6"
        lst = List(is_ordered=True)
    elif list_elm.name == "ul":
        assert assert_attr(list_elm, "class") == "calibre12"
        lst = List(is_ordered=False)
    else:
        error(list_elm)

    for elm in list_elm.children:
        li = assert_tag(elm, "li")
        assert assert_attr(li, "class") == "calibre10"

        list_item = ListItem()
        list_item += para_inside(li)
        lst += [list_item]

    return lst


def translate_layer(div: bs4.Tag, *, use_last_layer: Layer | None = None) -> Layer:
    layer = use_last_layer or Layer()

    for elm in div.children:
        if isinstance(elm, bs4.NavigableString):
            continue
        assert isinstance(elm, bs4.Tag)

        ident = elm.attrs.get("id")
        if ident in NON_UNIQUE_IDENT:
            ident = None

        sub_ast: AST | None = None
        match elm.name:
            case "p":
                para: Para | None = None
                klass = elm.attrs.get("class")
                match klass:
                    case "softbreak":
                        continue
                    case (
                        None
                        | "calibre3"
                        | "ctxind"
                        | "blocks"
                        | "blocksind"
                        | "blocksind1"
                    ):
                        para = Para()
                    case "img" | "img1":
                        para = Para()
                    case (
                        "bmh"
                        | "fmh"
                        | "fmh1"
                        | "fmh2"
                        | "fmh3"
                        | "fmh4"
                        | "fmh5"
                        | "fmh6"
                        | "csht"
                    ):
                        layer.title = elm.text
                        layer.ident = ident
                        continue
                    case "cht" | "csht1" | "auth":
                        para = Para(center=True, italic=True)
                    case "blockc" | "centers" | "center" | "blockci":
                        para = Para(center=True)
                    case "right":
                        para = Para(right=True)
                    case "ctxtop" | "ctxtop1" | "ctx" | "ctx1":
                        para = Para(para_indent=0)
                    case "blockpara" | "sidebar":
                        para = QuotePara()
                    case "lists" | "liste" | "liste1":
                        para = Poetry(para_indent=2)
                    case "list1" | "list":
                        para = Poetry(para_indent=1)
                    case "listm" | "listm1" | "listm2":
                        para = Poetry(para_indent=0, center=True)
                    case "pcenter":
                        para = ImgCaption(italic=True)
                    case "centerm":
                        para = ImgCaption(italic=True, bold=True)

                    # 脚注内容章节的标题
                    case "ntsh" | "ntsh1":
                        para = Para(center=True, bold=True)
                    # 脚注内容和引用
                    case "nt" | "ntstx" | "bibtx":
                        para = Para(word_indent="non-first-line")

                if para is None:
                    error(elm)
                para += para_inside(elm)
                sub_ast = para

            case "div":
                assert elm.attrs.get("class") == "calibre1"
                sub_ast = translate_layer(elm)
            case "ol" | "ul":
                sub_ast = translate_list(elm)
            case "h2":
                layer.title = elm.text
                layer.ident = ident
                continue
            case _:
                error(elm)

        assert sub_ast is not None
        sub_ast.ident = ident
        layer += [sub_ast]

    return layer


def translate(book_name: str) -> AST:
    book = epub.read_epub(book_name)
    book_layer = Layer()

    layer: Layer | None = None
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            if item.get_name() in EXCLUDES:
                continue
            # print(item.get_name())

            soup = BeautifulSoup(item.get_content(), features="xml")
            assert (body := soup.select_one("body"))

            children = [
                elm
                for elm in body.children
                if isinstance(elm, bs4.Tag) and elm.name == "div"
            ]
            assert len(children) == 1
            character_elm = children[0]
            character_elm = assert_tag(character_elm, "div")
            assert assert_attr(character_elm, "class") == "calibre1"

            if "split" in item.get_name() and "_000" not in item.get_name():
                print(
                    f"Reuse last layer: {type(layer)} ({item.get_name()})",
                    file=sys.stderr,
                )
                layer = translate_layer(character_elm, use_last_layer=layer)
            else:
                layer = translate_layer(character_elm)
                book_layer += [layer]

    return book_layer


r"""
body {
    p.fmh\d 标题 
    p.csht1 标题下边的一小段注释, 有时也是作者
    p.auth > em.calibre8 作者, 同标题下注释样式

    .calibre1 { : 小节容器
        p.csht 小节标题
        p.ctx1 顶格正文段落
    }

    p.ctxtop: 顶格正文段落
    p.ctx 顶格段落
    p.blocks/calibre3 段落
    p.blocksind 段落?

    p.blockpara 整段引用
    p.ctxind: 整段引用之后的一段和正文段落样式一样的解释段落
}

p.blockc 居中段落
p.centers


p.lists 多缩进一格的诗歌开头
p.liste 多缩进一格的诗歌后续
p.liste1

p.list1 只缩进一格的诗歌
p.list

p.sidebar 斜体居中的东西, 疑似是某种强调化的引用

p.pcenter 跟在图片前边的居中的图片描述, 只是斜体, 不粗
p.centerm 跟在图片前边的居中的图片描述, 但是粗斜体
p.img1 > img[src=(.*)].calibre2 图片
有时也会有单个的 img.calibre2 表示行内图片

small.calibre5 全大写的人名
em.calibre4 斜体引用
p.calibre4 书信大段斜体正文
sup > a#nr\d > a[href=(.*)] 上标

p.right 人名在右边

calibre5: 0.75em
p.ctxtop <首字母> small.calibre5 大写字母
    段首那个好看的大的一小段大写字母的样式
有时也用 small.calibre11
有时也用 span.dropcaps

b.calibre7: 粗体
calibre8: 行宽 1.2 的斜体


Book2 Ch 51 (389) 有若干个表
Book3 Ch 11 (455) 有若干个表
table

part0220 是 footnotes
    p.ntsh 粗体居中小标题
    p.ntstx#nt(\d) > (a[href] > b.calibre7 > $1) text
part0221 是 Bibliography
    p.bibtx 
part0226 是 index
"""
