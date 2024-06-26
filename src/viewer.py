import sys
from typing import Iterable, cast

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual import log, widget
from textual.reactive import var
from textual.widgets import Header, Footer, Static

from bytecode_widget import BytecodeWidget
from events import HoverLine
from ast_widget import ASTWidget
from token_widget import TokenWidget
from source_widget import SourceWidget
from editor import EditorScreen

# This controls 3.13 features
VERSION_3_13 = sys.version_info >= (3, 13)


def widget_with_title(w: widget.Widget, title: str) -> Iterable[widget.Widget]:
    with Vertical():
        yield Static(title, classes="title")
        yield w


class CodeViewer(App[None]):

    TITLE = "Compiler Pipeline Explorer"
    CSS_PATH = "viewer.tcss"
    SCREENS = {"editor": EditorScreen()}

    startup_code: str = ""

    if VERSION_3_13:
        BINDINGS = [
            ("q,escape", "quit", "Quit"),
            ("e", "open_editor", "Editor"),
            ("1", "toggle_source", "Source"),
            ("2", "toggle_tokens", "Tokens"),
            ("3", "toggle_ast", "AST"),
            ("4", "toggle_opt_ast", "AST(opt.)"),
            ("5", "toggle_pseudo_bc", "Pseudo BC"),
            ("6", "toggle_opt_pseudo_bc", "Opt. BC"),
            ("7", "toggle_code_obj", "Final BC"),
        ]
    else:
        BINDINGS = [  # type: ignore
            ("q,escape", "quit", "Quit"),
            ("e", "open_editor", "Editor"),
            ("1", "toggle_source", "Source"),
            ("2", "toggle_tokens", "Tokens"),
            ("3", "toggle_ast", "AST"),
            ("7", "toggle_code_obj", "Final BC"),
        ]

    show_source = var(True)
    show_tokens = var(False)
    show_ast = var(False)
    show_opt_ast = var(False)
    show_pseudo_bc = var(False)
    show_opt_pseudo_bc = var(False)
    show_code_obj = var(True)

    def update_visibility(self, id: str, visible: bool) -> None:
        self.query_one(f"#{id}").parent.styles.display = "block" if visible else "none"
        visible_panels = (
            self.show_source
            + self.show_tokens
            + self.show_ast
            + self.show_opt_ast
            + self.show_pseudo_bc
            + self.show_opt_pseudo_bc
            + self.show_code_obj
        )
        self.query_one("#body").styles.grid_size_columns = min(visible_panels, 3)

    def watch_show_source(self, show_source: bool) -> None:
        self.update_visibility("source", show_source)

    def watch_show_tokens(self, show_tokens: bool) -> None:
        self.update_visibility("tokens", show_tokens)

    def watch_show_ast(self, show_ast: bool) -> None:
        self.update_visibility("ast", show_ast)

    if VERSION_3_13:

        def watch_show_opt_ast(self, show_opt_ast: bool) -> None:
            self.update_visibility("opt-ast", show_opt_ast)

        def watch_show_pseudo_bc(self, show_pseudo_bc: bool) -> None:
            self.update_visibility("pseudo-bc", show_pseudo_bc)

        def watch_show_opt_pseudo_bc(self, show_opt_pseudo_bc: bool) -> None:
            self.update_visibility("opt-pseudo-bc", show_opt_pseudo_bc)

    def watch_show_code_obj(self, show_code_obj: bool) -> None:
        self.update_visibility("opt-code-obj", show_code_obj)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="body"):
            yield from widget_with_title(SourceWidget(id="source"), "Source (1)")
            yield from widget_with_title(TokenWidget(id="tokens"), "Tokens (2)")
            yield from widget_with_title(ASTWidget(id="ast"), "AST (3)")
            if VERSION_3_13:
                yield from widget_with_title(
                    ASTWidget(id="opt-ast", optimized=True), "Optimized AST (4)"
                )
                yield from widget_with_title(
                    BytecodeWidget(id="pseudo-bc", mode="pseudo"), "Pseudo Bytecode (5)"
                )
                yield from widget_with_title(
                    BytecodeWidget(id="opt-pseudo-bc", mode="optimized"),
                    "Optimized Pseudo Bytecode (6)",
                )
            yield from widget_with_title(
                BytecodeWidget(id="opt-code-obj", mode="compiled"),
                "Assembled Bytecode (7)",
            )
        yield Footer()

    def set_code(self, code: str) -> None:
        cast(EditorScreen, self.SCREENS["editor"]).set_code(code)
        source = self.query_one("#source", SourceWidget)
        source.set_code(code)
        self.query_one("#tokens", TokenWidget).set_code(code)
        self.query_one("#ast", ASTWidget).set_code(code)
        if VERSION_3_13:
            self.query_one("#opt-ast", ASTWidget).set_code(code)
            self.query_one("#pseudo-bc", BytecodeWidget).set_code(code)
            self.query_one("#opt-pseudo-bc", BytecodeWidget).set_code(code)
        self.query_one("#opt-code-obj", BytecodeWidget).set_code(code)

    def on_mount(self) -> None:
        self.set_code(self.startup_code)
        self.query_one(".editor").focus()

    def action_toggle_source(self) -> None:
        self.show_source = not self.show_source

    def action_toggle_tokens(self) -> None:
        self.show_tokens = not self.show_tokens

    def action_toggle_ast(self) -> None:
        self.show_ast = not self.show_ast

    def action_toggle_opt_ast(self) -> None:
        self.show_opt_ast = not self.show_opt_ast

    def action_toggle_pseudo_bc(self) -> None:
        self.show_pseudo_bc = not self.show_pseudo_bc

    def action_toggle_opt_pseudo_bc(self) -> None:
        self.show_opt_pseudo_bc = not self.show_opt_pseudo_bc

    def action_toggle_code_obj(self) -> None:
        self.show_code_obj = not self.show_code_obj

    def action_open_editor(self) -> None:
        def update_code(code: str | None) -> None:
            if code is not None:
                self.set_code(code)

        self.push_screen("editor", update_code)

    def on_hover_line(self, message: HoverLine) -> None:
        log(f"hover: {message.lineno}")
        source = self.query_one("#source", SourceWidget)
        source.highlight(message.lineno)
        tokens = self.query_one("#tokens", TokenWidget)
        tokens.highlight(message.lineno)
        ast = self.query_one("#ast", ASTWidget)
        ast.highlight(message.lineno)
        if VERSION_3_13:
            opt_ast = self.query_one("#opt-ast", ASTWidget)
            opt_ast.highlight(message.lineno)
            pseudo_bc = self.query_one("#pseudo-bc", BytecodeWidget)
            pseudo_bc.highlight(message.lineno)
            opt_pseudo_bc = self.query_one("#opt-pseudo-bc", BytecodeWidget)
            opt_pseudo_bc.highlight(message.lineno)
        opt_code_obj = self.query_one("#opt-code-obj", BytecodeWidget)
        opt_code_obj.highlight(message.lineno)


if __name__ == "__main__":
    app = CodeViewer()
    app.startup_code = """
"Fibonacci Demo"

a, b = 0, 1
for _ in range(12):
    a, b = b, a+b
    print(a)

del a
del b
"""
    app.run()
