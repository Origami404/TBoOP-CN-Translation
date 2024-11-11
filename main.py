from extract.translate import translate
from extract.ast import print_ast
from extract.output import OutputTypst

if __name__ == "__main__":
    BOOK_NAME = ".local/TBOP.epub"
    ast = translate(BOOK_NAME)
    print_ast(ast)

    OUTPUT_FOLDER = ".local/output"
    outputer = OutputTypst(OUTPUT_FOLDER)
    outputer.output_book(ast)
