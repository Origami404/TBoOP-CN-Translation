from extract.translate import translate
from extract.ast import print_ast


if __name__ == "__main__":
    BOOK_NAME = ".local/TBOP.epub"
    ast = translate(BOOK_NAME)
    print_ast(ast)
