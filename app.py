from __future__ import annotations

import math
import random
import statistics
import tkinter as tk
from collections import Counter
from dataclasses import dataclass, field
from tkinter import messagebox, simpledialog, ttk


DART_NUMBERS = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
MAX_THROWS = 15
AIMED_MAX_THROWS = 10
DARTS_PER_THROW = 3
COUNTDOWN_GAMES = {"501": 501, "301": 301}
AIMED_GAME = "Aimed"


@dataclass
class Player:
    name: str
    score: int = 0
    throw_count: int = 0
    bust_rows: set[int] = field(default_factory=set)
    throws: list[list[int | None]] = field(
        default_factory=lambda: [[None, None, None] for _ in range(MAX_THROWS)]
    )


class DartScoreApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Dart Score")
        self.geometry("1220x760")
        self.minsize(1040, 680)

        self.players: list[Player] = []
        self.game_mode = tk.StringVar(value="501")
        self.current_player_idx = 0
        self.dart_in_turn = 0
        self.turn_scores: list[int] = []
        self.turn_start_score = 0
        self.pending_turn_complete = False
        self.match_over = False
        self.aimed_targets: list[int | None] = [None] * MAX_THROWS

        self.score_labels: dict[int, tk.Label] = {}
        self.throw_cells: dict[tuple[int, int, int], tk.Label] = {}
        self.sum_cells: dict[tuple[int, int], tk.Label] = {}
        self.stats_labels: dict[int, tk.Label] = {}
        self.stats_histograms: dict[int, tk.Canvas] = {}
        self.scoreboard_canvas: tk.Canvas | None = None
        self.turn_label: tk.Label | None = None
        self.dart_label: tk.Label | None = None
        self.throw_label: tk.Label | None = None
        self.status_label: tk.Label | None = None
        self.next_turn_button: ttk.Button | None = None
        self.board_canvas: tk.Canvas | None = None

        self._configure_style()
        self.show_setup_screen()

    def _configure_style(self) -> None:
        self.configure(bg="#f4f0e6")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f0e6")
        style.configure("Card.TFrame", background="#fffaf0", relief="flat")
        style.configure("TLabel", background="#f4f0e6", foreground="#241f1b", font=("DejaVu Sans", 11))
        style.configure("Title.TLabel", font=("DejaVu Serif", 30, "bold"), foreground="#22160f")
        style.configure("Subtitle.TLabel", font=("DejaVu Sans", 13), foreground="#5c4c3f")
        style.configure("TButton", font=("DejaVu Sans", 11, "bold"), padding=8)
        style.configure("TRadiobutton", background="#f4f0e6", foreground="#241f1b", font=("DejaVu Sans", 12))

    def clear(self) -> None:
        for widget in self.winfo_children():
            widget.destroy()

    def show_setup_screen(self) -> None:
        self.clear()
        container = ttk.Frame(self, padding=36)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Dart Score", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            container,
            text="Enter players, choose a game, then play one leg with up to 15 throws per player, or 10 in Aimed.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 28))

        form = ttk.Frame(container, style="Card.TFrame", padding=24)
        form.pack(fill="both", expand=True)

        ttk.Label(form, text="Players", font=("DejaVu Sans", 14, "bold"), background="#fffaf0").pack(anchor="w")
        ttk.Label(
            form,
            text="One player name per line. At least two players are required.",
            background="#fffaf0",
            foreground="#66584c",
        ).pack(anchor="w", pady=(0, 8))

        self.players_text = tk.Text(
            form,
            height=10,
            width=42,
            font=("DejaVu Sans", 14),
            bg="#fffdf7",
            fg="#241f1b",
            insertbackground="#241f1b",
            relief="solid",
            bd=1,
        )
        self.players_text.insert("1.0", "Player 1\nPlayer 2")
        self.players_text.pack(anchor="w", fill="x", pady=(0, 18))

        ttk.Label(form, text="Game", font=("DejaVu Sans", 14, "bold"), background="#fffaf0").pack(anchor="w")
        game_row = ttk.Frame(form, style="Card.TFrame")
        game_row.pack(anchor="w", pady=(8, 22))
        ttk.Radiobutton(game_row, text="501", variable=self.game_mode, value="501").pack(side="left", padx=(0, 18))
        ttk.Radiobutton(game_row, text="301", variable=self.game_mode, value="301").pack(side="left", padx=(0, 18))
        ttk.Radiobutton(game_row, text="Aimed", variable=self.game_mode, value=AIMED_GAME).pack(side="left")

        ttk.Button(form, text="Start Game", command=self.start_match).pack(anchor="w")

    def start_match(self) -> None:
        names = [line.strip() for line in self.players_text.get("1.0", "end").splitlines() if line.strip()]
        if len(names) < 2:
            messagebox.showerror("Players required", "Enter at least two player names.")
            return

        self.players = [Player(name=name, score=self.starting_score()) for name in names]
        self.current_player_idx = 0
        self.dart_in_turn = 0
        self.turn_scores = []
        self.turn_start_score = self.players[0].score
        self.pending_turn_complete = False
        self.match_over = False
        self.aimed_targets = [None] * MAX_THROWS
        self.ensure_aimed_target(0)
        self.show_game_screen()
        self.refresh_status()

    def is_aimed_game(self) -> bool:
        return self.game_mode.get() == AIMED_GAME

    def starting_score(self) -> int:
        return 0 if self.is_aimed_game() else COUNTDOWN_GAMES[self.game_mode.get()]

    def game_title(self) -> str:
        if self.is_aimed_game():
            return f"{AIMED_GAME} | {self.game_throw_limit()} throws"
        return f"{self.game_mode.get()} | {self.game_throw_limit()} throws per player"

    def game_throw_limit(self) -> int:
        return AIMED_MAX_THROWS if self.is_aimed_game() else MAX_THROWS

    def ensure_aimed_target(self, throw_idx: int) -> int | None:
        if not self.is_aimed_game():
            return None

        if throw_idx >= self.game_throw_limit():
            return None

        target = self.aimed_targets[throw_idx]
        if target is None:
            target = random.randint(1, 20)
            self.aimed_targets[throw_idx] = target
        return target

    def aimed_score_value(self, raw_value: int, label: str, target: int | None) -> int:
        if target is None or label in {"MISS", "B25", "B50"}:
            return 0

        board_number = ""
        for char in label[1:]:
            if not char.isdigit():
                break
            board_number += char

        if not board_number or int(board_number) != target:
            return 0
        return raw_value

    def show_game_screen(self) -> None:
        self.clear()
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=0)
        root.rowconfigure(0, weight=1)

        left = ttk.Frame(root, padding=12, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        right = ttk.Frame(root, padding=12, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="ns")

        self._build_scoreboard(left)
        self._build_control_panel(left)
        self._build_dartboard(right)

    def _build_scoreboard(self, parent: ttk.Frame) -> None:
        holder = tk.Frame(parent, bg="#fffaf0")
        holder.grid(row=0, column=0, sticky="nsew")
        holder.rowconfigure(2, weight=1)
        holder.columnconfigure(0, weight=1)

        header = tk.Label(
            holder,
            text=self.game_title(),
            bg="#fffaf0",
            fg="#241f1b",
            font=("DejaVu Serif", 22, "bold"),
        )
        header.grid(row=0, column=0, sticky="w", pady=(0, 10))

        fixed_canvas = tk.Canvas(holder, height=104, bg="#fffaf0", highlightthickness=0)
        fixed_header = tk.Frame(fixed_canvas, bg="#fffaf0")
        fixed_window_id = fixed_canvas.create_window((0, 0), window=fixed_header, anchor="nw")
        fixed_canvas.grid(row=1, column=0, sticky="ew")

        body_canvas = tk.Canvas(holder, bg="#fffaf0", highlightthickness=0)
        self.scoreboard_canvas = body_canvas
        y_scroll = ttk.Scrollbar(holder, orient="vertical", command=body_canvas.yview)
        x_scroll = ttk.Scrollbar(holder, orient="horizontal")
        body_table = tk.Frame(body_canvas, bg="#fffaf0")
        body_window_id = body_canvas.create_window((0, 0), window=body_table, anchor="nw")

        def scroll_x(*args: str) -> None:
            fixed_canvas.xview(*args)
            body_canvas.xview(*args)

        def sync_body_xview(first: str, last: str) -> None:
            x_scroll.set(first, last)
            fixed_canvas.xview_moveto(float(first))

        def scroll_horizontal(event: tk.Event) -> str:
            delta = -1 if event.delta > 0 else 1
            scroll_x("scroll", str(delta), "units")
            return "break"

        x_scroll.configure(command=scroll_x)
        body_canvas.configure(yscrollcommand=y_scroll.set, xscrollcommand=sync_body_xview)
        fixed_canvas.bind("<Shift-MouseWheel>", scroll_horizontal)
        body_canvas.bind("<Shift-MouseWheel>", scroll_horizontal)
        body_canvas.grid(row=2, column=0, sticky="nsew")
        y_scroll.grid(row=2, column=1, sticky="ns")
        x_scroll.grid(row=3, column=0, sticky="ew")

        def update_fixed_region(_event: tk.Event) -> None:
            fixed_canvas.configure(scrollregion=fixed_canvas.bbox("all"))

        def update_body_region(_event: tk.Event) -> None:
            body_canvas.configure(scrollregion=body_canvas.bbox("all"))

        def stretch_fixed(event: tk.Event) -> None:
            requested = fixed_header.winfo_reqwidth()
            fixed_canvas.itemconfigure(fixed_window_id, width=max(event.width, requested))

        def stretch_body(event: tk.Event) -> None:
            requested = body_table.winfo_reqwidth()
            body_canvas.itemconfigure(body_window_id, width=max(event.width, requested))

        fixed_header.bind("<Configure>", update_fixed_region)
        body_table.bind("<Configure>", update_body_region)
        fixed_canvas.bind("<Configure>", stretch_fixed)
        body_canvas.bind("<Configure>", stretch_body)

        self.score_labels.clear()
        self.throw_cells.clear()
        self.sum_cells.clear()
        self.stats_labels.clear()
        self.stats_histograms.clear()

        throw_col_width = 68
        dart_col_width = 52
        player_group_width = dart_col_width * 4
        for column in range(1 + len(self.players) * 4):
            width = throw_col_width if column == 0 else dart_col_width
            fixed_header.columnconfigure(column, minsize=width, weight=0)
            body_table.columnconfigure(column, minsize=width, weight=0)

        tk.Label(fixed_header, text="", width=8, bg="#2f261f", fg="#fff8ec").grid(
            row=0, column=0, rowspan=3, sticky="nsew", padx=1, pady=1
        )

        for player_idx, player in enumerate(self.players):
            base_col = 1 + player_idx * 4
            name_frame = tk.Frame(fixed_header, width=player_group_width, bg="#2f261f")
            name_frame.grid(row=0, column=base_col, columnspan=4, sticky="nsew", padx=1, pady=1)
            name_frame.grid_propagate(False)
            tk.Label(
                name_frame,
                text=player.name,
                bg="#2f261f",
                fg="#fff8ec",
                font=("DejaVu Sans", 12, "bold"),
                padx=6,
                pady=6,
            ).pack(fill="both", expand=True)

            score_frame = tk.Frame(fixed_header, width=player_group_width, bg="#f7c76f")
            score_frame.grid(row=1, column=base_col, columnspan=4, sticky="nsew", padx=1, pady=1)
            score_frame.grid_propagate(False)
            score = tk.Label(
                score_frame,
                text=str(player.score),
                bg="#f7c76f",
                fg="#241f1b",
                font=("DejaVu Sans", 16, "bold"),
                padx=6,
                pady=7,
            )
            score.pack(fill="both", expand=True)
            self.score_labels[player_idx] = score

            sum_label = "Tgt/Sum" if self.is_aimed_game() else "Sum"
            for offset, label in enumerate(("D1", "D2", "D3", sum_label)):
                tk.Label(
                    fixed_header,
                    text=label,
                    width=6,
                    bg="#4b3a2e",
                    fg="#fff8ec",
                    font=("DejaVu Sans", 10, "bold"),
                    padx=3,
                    pady=5,
                ).grid(row=2, column=base_col + offset, sticky="nsew", padx=1, pady=1)

        tk.Label(
            fixed_header,
            text="Throw",
            width=8,
            bg="#4b3a2e",
            fg="#fff8ec",
            font=("DejaVu Sans", 10, "bold"),
            padx=3,
            pady=5,
        ).grid(row=2, column=0, sticky="nsew", padx=1, pady=1)

        for throw_idx in range(self.game_throw_limit()):
            tk.Label(
                body_table,
                text=str(throw_idx + 1),
                width=8,
                bg="#f7e4bb",
                fg="#241f1b",
                font=("DejaVu Sans", 10, "bold"),
                pady=6,
            ).grid(row=throw_idx, column=0, sticky="nsew", padx=1, pady=1)
            for player_idx in range(len(self.players)):
                base_col = 1 + player_idx * 4
                for dart_idx in range(DARTS_PER_THROW):
                    cell = tk.Label(
                        body_table,
                        text="",
                        width=6,
                        bg="#fffdf7",
                        fg="#241f1b",
                        font=("DejaVu Sans", 10, "bold"),
                        pady=6,
                    )
                    cell.grid(row=throw_idx, column=base_col + dart_idx, sticky="nsew", padx=1, pady=1)
                    cell.bind(
                        "<Button-1>",
                        lambda _event, p=player_idx, t=throw_idx, d=dart_idx: self.edit_score_cell(p, t, d),
                    )
                    self.throw_cells[(player_idx, throw_idx, dart_idx)] = cell
                sum_cell = tk.Label(
                    body_table,
                    text="",
                    width=6,
                    bg="#fff7e8",
                    fg="#241f1b",
                    font=("DejaVu Sans", 10, "bold"),
                    pady=6,
                )
                sum_cell.grid(row=throw_idx, column=base_col + 3, sticky="nsew", padx=1, pady=1)
                self.sum_cells[(player_idx, throw_idx)] = sum_cell

        stats_canvas = tk.Canvas(holder, height=210, bg="#fffaf0", highlightthickness=0)
        stats_scroll = ttk.Scrollbar(holder, orient="horizontal", command=stats_canvas.xview)
        stats_frame = tk.Frame(stats_canvas, bg="#fffaf0")
        stats_window_id = stats_canvas.create_window((0, 0), window=stats_frame, anchor="nw")
        stats_canvas.configure(xscrollcommand=stats_scroll.set)
        stats_canvas.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        stats_scroll.grid(row=5, column=0, sticky="ew")

        def update_stats_region(_event: tk.Event) -> None:
            stats_canvas.configure(scrollregion=stats_canvas.bbox("all"))

        def keep_stats_height(event: tk.Event) -> None:
            stats_canvas.itemconfigure(stats_window_id, height=event.height)

        def scroll_stats_horizontal(event: tk.Event) -> str:
            delta = -1 if event.delta > 0 else 1
            stats_canvas.xview_scroll(delta, "units")
            return "break"

        stats_frame.bind("<Configure>", update_stats_region)
        stats_canvas.bind("<Configure>", keep_stats_height)
        stats_canvas.bind("<Shift-MouseWheel>", scroll_stats_horizontal)

        for player_idx, player in enumerate(self.players):
            card = tk.Frame(stats_frame, width=260, bg="#fff7e8", highlightbackground="#e0cda7", highlightthickness=1)
            card.grid(row=0, column=player_idx, sticky="ns", padx=(0 if player_idx == 0 else 8, 0))
            card.grid_propagate(False)
            tk.Label(
                card,
                text=f"{player.name} statistics",
                bg="#fff7e8",
                fg="#241f1b",
                font=("DejaVu Sans", 11, "bold"),
                anchor="w",
                padx=8,
                pady=5,
            ).pack(fill="x")
            histogram = tk.Canvas(card, width=240, height=110, bg="#fff7e8", highlightthickness=0)
            histogram.pack(fill="x", padx=8, pady=(2, 4))
            label = tk.Label(
                card,
                text="",
                bg="#fff7e8",
                fg="#4b3a2e",
                font=("DejaVu Sans", 10),
                justify="left",
                anchor="nw",
                padx=8,
                pady=4,
            )
            label.pack(fill="both", expand=True)
            self.stats_histograms[player_idx] = histogram
            self.stats_labels[player_idx] = label
    def _build_control_panel(self, parent: ttk.Frame) -> None:
        panel = tk.Frame(parent, bg="#fffaf0")
        panel.grid(row=1, column=0, sticky="ew", pady=(18, 0))

        self.turn_label = tk.Label(panel, text="", bg="#fffaf0", fg="#241f1b", font=("DejaVu Serif", 20, "bold"))
        self.turn_label.pack(anchor="w")
        self.dart_label = tk.Label(panel, text="", bg="#fffaf0", fg="#66584c", font=("DejaVu Sans", 13))
        self.dart_label.pack(anchor="w", pady=(4, 0))
        self.throw_label = tk.Label(panel, text="Throws this turn: -", bg="#fffaf0", fg="#66584c", font=("DejaVu Sans", 12))
        self.throw_label.pack(anchor="w", pady=(4, 0))
        self.status_label = tk.Label(panel, text="", bg="#fffaf0", fg="#8f2d22", font=("DejaVu Sans", 12, "bold"))
        self.status_label.pack(anchor="w", pady=(8, 0))

        buttons = tk.Frame(panel, bg="#fffaf0")
        buttons.pack(anchor="w", pady=(14, 0))
        self.next_turn_button = ttk.Button(buttons, text="Next turn", command=self.next_turn)
        self.next_turn_button.pack(side="left", padx=(0, 10))
        ttk.Button(buttons, text="New Game", command=self.show_setup_screen).pack(side="left")
        self.refresh_status()

    def _build_dartboard(self, parent: ttk.Frame) -> None:
        tk.Label(parent, text="Click Score Board", bg="#fffaf0", fg="#241f1b", font=("DejaVu Serif", 20, "bold")).pack(anchor="w")
        canvas = tk.Canvas(parent, width=520, height=560, bg="#fffaf0", highlightthickness=0)
        canvas.pack(pady=(8, 0))
        self.board_canvas = canvas

        cx, cy = 260, 280
        radii = {
            "inner_bull": 17,
            "outer_bull": 37,
            "single_inner": 94,
            "triple_outer": 120,
            "single_outer": 178,
            "double_outer": 210,
        }

        canvas.create_oval(
            cx - radii["double_outer"] - 10,
            cy - radii["double_outer"] - 10,
            cx + radii["double_outer"] + 10,
            cy + radii["double_outer"] + 10,
            fill="#2a211b",
            outline="#2a211b",
        )

        for i, number in enumerate(DART_NUMBERS):
            start = i * 18 - 9
            end = i * 18 + 9
            base = "#f6ead3" if i % 2 == 0 else "#22201d"
            base_text = "#000000"
            double_triple = "#bf332b" if i % 2 == 0 else "#237a4b"
            self._sector(canvas, cx, cy, radii["triple_outer"], radii["single_outer"], start, end, base, f"S{number}", number)
            self._sector(canvas, cx, cy, radii["single_inner"], radii["triple_outer"], start, end, double_triple, f"T{number}", number * 3)
            self._sector(canvas, cx, cy, radii["outer_bull"], radii["single_inner"], start, end, base, f"S{number}inner", number)
            self._sector(canvas, cx, cy, radii["single_outer"], radii["double_outer"], start, end, double_triple, f"D{number}", number * 2)

            label_angle = math.radians(i * 18)
            lx = cx + math.sin(label_angle) * 238
            ly = cy - math.cos(label_angle) * 238
            canvas.create_text(lx, ly, text=str(number), fill=base_text, font=("DejaVu Sans", 13, "bold"))

        canvas.create_oval(
            cx - radii["outer_bull"],
            cy - radii["outer_bull"],
            cx + radii["outer_bull"],
            cy + radii["outer_bull"],
            fill="#237a4b",
            outline="#1a1714",
            width=2,
            tags=("score", "B25"),
        )
        canvas.create_oval(
            cx - radii["inner_bull"],
            cy - radii["inner_bull"],
            cx + radii["inner_bull"],
            cy + radii["inner_bull"],
            fill="#bf332b",
            outline="#1a1714",
            width=2,
            tags=("score", "B50"),
        )
        canvas.create_text(cx, cy - 54, text="25", fill="#fffaf0", font=("DejaVu Sans", 10, "bold"))
        canvas.create_text(cx, cy, text="50", fill="#fffaf0", font=("DejaVu Sans", 10, "bold"))

        canvas.tag_bind("score", "<Button-1>", self.on_board_click)
        ttk.Button(parent, text="Miss / 0", command=lambda: self.apply_throw(0, "MISS")).pack(fill="x", pady=(10, 0))

    def _sector(
        self,
        canvas: tk.Canvas,
        cx: int,
        cy: int,
        inner: int,
        outer: int,
        start_deg: float,
        end_deg: float,
        fill: str,
        tag: str,
        value: int,
    ) -> None:
        points: list[float] = []
        steps = 5
        for step in range(steps + 1):
            angle = math.radians(start_deg + (end_deg - start_deg) * step / steps)
            points.extend([cx + math.sin(angle) * outer, cy - math.cos(angle) * outer])
        for step in range(steps, -1, -1):
            angle = math.radians(start_deg + (end_deg - start_deg) * step / steps)
            points.extend([cx + math.sin(angle) * inner, cy - math.cos(angle) * inner])
        canvas.create_polygon(points, fill=fill, outline="#1a1714", width=1, tags=("score", tag, f"value:{value}"))

    def on_board_click(self, _event: tk.Event) -> None:
        if self.match_over or self.board_canvas is None:
            return
        item = self.board_canvas.find_withtag("current")
        if not item:
            return
        tags = self.board_canvas.gettags(item[0])
        value = next((int(tag.split(":", 1)[1]) for tag in tags if tag.startswith("value:")), None)
        label = next((tag for tag in tags if tag not in {"score"} and not tag.startswith("value:")), "")
        if value is None:
            if "B25" in tags:
                value, label = 25, "B25"
            elif "B50" in tags:
                value, label = 50, "B50"
            else:
                return
        self.apply_throw(value, label)

    def apply_throw(self, value: int, label: str) -> None:
        if self.match_over or self.pending_turn_complete:
            return
        player = self.players[self.current_player_idx]
        throw_idx = self.current_throw_index(player)
        if throw_idx >= self.game_throw_limit():
            self.pending_turn_complete = True
            self.refresh_status()
            return

        if self.dart_in_turn == 0:
            self.ensure_aimed_target(throw_idx)
            self.turn_start_score = player.score
            self.turn_scores = []

        target = self.aimed_targets[throw_idx] if self.is_aimed_game() else None
        scored_value = self.aimed_score_value(value, label, target) if self.is_aimed_game() else value

        player.throws[throw_idx][self.dart_in_turn] = scored_value
        if self.is_aimed_game():
            player.score += scored_value
        else:
            player.score -= scored_value
        self.dart_in_turn += 1
        self.turn_scores.append(scored_value)
        if self.is_aimed_game():
            self.status_label.config(text=f"{player.name}: {label} scores {scored_value} (target {target}).")
        else:
            self.status_label.config(text=f"{player.name}: {label} = {scored_value}")

        if not self.is_aimed_game() and player.score == 0:
            self.refresh_scoreboard()
            self.finish_game(player)
            return
        if not self.is_aimed_game() and player.score < 0:
            player.score = self.turn_start_score
            player.bust_rows.add(throw_idx)
            self.refresh_scoreboard()
            self.status_label.config(text=f"Bust. {player.name} returns to {player.score}.")
            self.pending_turn_complete = True
            self.refresh_status()
            return

        self.refresh_scoreboard()
        if self.dart_in_turn >= DARTS_PER_THROW:
            self.pending_turn_complete = True
            self.status_label.config(text=f"{player.name} finished this turn. Click Next turn.")
            self.refresh_status()
        else:
            self.refresh_status()

    def edit_score_cell(self, player_idx: int, throw_idx: int, dart_idx: int) -> None:
        if self.match_over:
            return

        player = self.players[player_idx]
        current_value = player.throws[throw_idx][dart_idx]
        if current_value is None:
            return

        edited_value = simpledialog.askinteger(
            "Edit score",
            f"{player.name}, throw {throw_idx + 1}, dart {dart_idx + 1}:",
            initialvalue=current_value,
            minvalue=0,
            maxvalue=60,
            parent=self,
        )
        if edited_value is None:
            return

        player.throws[throw_idx][dart_idx] = edited_value
        if player_idx == self.current_player_idx and throw_idx == self.current_throw_index(player):
            self.turn_scores = [score for score in player.throws[throw_idx][: self.dart_in_turn] if score is not None]

        self.recompute_scores_from_scoreboard()
        if self.status_label:
            self.status_label.config(text=f"Edited {player.name}: dart {dart_idx + 1} is now {edited_value}.")
        self.refresh_status()

    def next_turn(self) -> None:
        if self.match_over or not self.pending_turn_complete:
            return

        player = self.players[self.current_player_idx]
        if self.dart_in_turn > 0 and player.throw_count < self.game_throw_limit():
            player.throw_count += 1

        self.dart_in_turn = 0
        self.turn_scores = []
        self.pending_turn_complete = False

        if self.all_throw_rows_used():
            self.finish_by_final_score()
            return

        self.current_player_idx = self.next_player_with_available_throw()
        self.turn_start_score = self.players[self.current_player_idx].score
        self.ensure_aimed_target(self.current_throw_index(self.players[self.current_player_idx]))
        self.refresh_status()

    def rows_to_score(self, player_idx: int, player: Player) -> int:
        rows = player.throw_count
        if player_idx == self.current_player_idx and (self.dart_in_turn > 0 or self.pending_turn_complete):
            rows = max(rows, player.throw_count + 1)
        return min(rows, self.game_throw_limit())

    def recompute_scores_from_scoreboard(self) -> None:
        for player_idx, player in enumerate(self.players):
            score = self.starting_score()
            bust_rows: set[int] = set()

            for row_idx in range(self.rows_to_score(player_idx, player)):
                if self.is_aimed_game():
                    score += sum(value for value in player.throws[row_idx] if value is not None)
                    continue

                row_start_score = score
                for value in player.throws[row_idx]:
                    if value is None:
                        continue
                    score -= value
                    if score < 0:
                        score = row_start_score
                        bust_rows.add(row_idx)
                        break

            player.score = score
            player.bust_rows = bust_rows

    def current_throw_index(self, player: Player) -> int:
        return player.throw_count

    def all_throw_rows_used(self) -> bool:
        return all(player.throw_count >= self.game_throw_limit() for player in self.players)

    def next_player_with_available_throw(self) -> int:
        for offset in range(1, len(self.players) + 1):
            idx = (self.current_player_idx + offset) % len(self.players)
            if self.players[idx].throw_count < self.game_throw_limit():
                return idx
        return self.current_player_idx

    def finish_game(self, winner: Player) -> None:
        self.match_over = True
        self.refresh_status()
        messagebox.showinfo("Game finished", f"{winner.name} wins by reaching zero.")

    def finish_by_final_score(self) -> None:
        self.match_over = True
        if self.is_aimed_game():
            best_score = max(player.score for player in self.players)
            winners = [player.name for player in self.players if player.score == best_score]
            result = f"All {self.game_throw_limit()} throw rows are used. Highest score: {', '.join(winners)} ({best_score})."
        else:
            best_score = min(player.score for player in self.players)
            winners = [player.name for player in self.players if player.score == best_score]
            result = f"All {self.game_throw_limit()} throw rows are used. Lowest remaining score: {', '.join(winners)}."
        self.refresh_status()
        messagebox.showinfo("Game finished", result)

    def player_dart_scores(self, player: Player) -> list[int]:
        return [score for throw in player.throws for score in throw if score is not None]

    def draw_histogram(self, player_idx: int, scores: list[int]) -> None:
        canvas = self.stats_histograms[player_idx]
        canvas.delete("all")
        width = max(canvas.winfo_width(), 240)
        height = 110
        left_pad = 26
        right_pad = 4
        top_pad = 14
        bottom_pad = 30
        plot_width = max(24, width - left_pad - right_pad)
        plot_height = height - top_pad - bottom_pad

        canvas.create_line(left_pad, top_pad, left_pad, top_pad + plot_height, fill="#7a6756")
        canvas.create_line(left_pad, top_pad + plot_height, width - right_pad, top_pad + plot_height, fill="#7a6756")

        if not scores:
            font_size = 8 if width < 150 else 10
            canvas.create_text(width / 2, height / 2, text="No throws", fill="#66584c", font=("DejaVu Sans", font_size))
            return

        counts = Counter(scores)
        values = sorted(counts)
        max_count = max(counts.values())
        gap = 3
        bar_width = max(4, (plot_width - gap * (len(values) - 1)) / max(len(values), 1))
        label_size = 7
        value_angle = 45

        for index, value in enumerate(values):
            count = counts[value]
            x0 = left_pad + index * (bar_width + gap)
            x1 = x0 + bar_width
            bar_height = plot_height * count / max_count
            y0 = top_pad + plot_height - bar_height
            y1 = top_pad + plot_height
            canvas.create_rectangle(x0, y0, x1, y1, fill="#bf6f30", outline="#8f4c20")
            label_x = (x0 + x1) / 2
            canvas.create_text(label_x, max(top_pad + 4, y0 - 5), text=str(count), fill="#4b3a2e", font=("DejaVu Sans", label_size))
            canvas.create_text(label_x, y1 + 13, text=str(value), fill="#4b3a2e", font=("DejaVu Sans", label_size), angle=value_angle)

    def format_player_stats(self, player: Player) -> str:
        scores = self.player_dart_scores(player)
        if not scores:
            return "Mean: -\nMedian: -\nStd dev: -"

        mean_value = statistics.mean(scores)
        median_value = statistics.median(scores)
        stdev_value = statistics.pstdev(scores) if len(scores) > 1 else 0.0
        return (
            f"Mean: {mean_value:.2f}\n"
            f"Median: {median_value:.2f}\n"
            f"Std dev: {stdev_value:.2f}"
        )

    def scroll_to_current_input(self) -> None:
        if self.scoreboard_canvas is None or self.match_over:
            return

        player = self.players[self.current_player_idx]
        throw_limit = self.game_throw_limit()
        throw_idx = min(self.current_throw_index(player), throw_limit - 1)
        block_start = min(throw_idx, max(0, throw_limit - 4))
        block_end = min(throw_limit - 1, block_start + 3)

        first_cell = self.throw_cells.get((self.current_player_idx, block_start, 0))
        last_row_cell = self.throw_cells.get((self.current_player_idx, block_end, 0))
        sum_cell = self.sum_cells.get((self.current_player_idx, block_start))
        if first_cell is None or last_row_cell is None or sum_cell is None:
            return

        self.update_idletasks()
        canvas = self.scoreboard_canvas
        scrollregion = canvas.bbox("all")
        if scrollregion is None:
            return

        _, _, total_width, total_height = scrollregion
        visible_left = canvas.canvasx(0)
        visible_top = canvas.canvasy(0)
        visible_width = canvas.winfo_width()
        visible_height = canvas.winfo_height()

        group_left = first_cell.winfo_x()
        group_right = sum_cell.winfo_x() + sum_cell.winfo_width()
        block_top = first_cell.winfo_y()
        block_bottom = last_row_cell.winfo_y() + last_row_cell.winfo_height()
        margin = 8

        target_left = visible_left
        if group_left < visible_left + margin:
            target_left = max(0, group_left - margin)
        elif group_right > visible_left + visible_width - margin:
            target_left = min(total_width - visible_width, group_right - visible_width + margin)

        target_top = visible_top
        if block_top < visible_top + margin or block_bottom > visible_top + visible_height - margin:
            target_top = min(max(0, block_top - margin), max(0, total_height - visible_height))

        if total_width > visible_width:
            canvas.xview_moveto(max(0.0, min(1.0, target_left / total_width)))
        if total_height > visible_height:
            canvas.yview_moveto(max(0.0, min(1.0, target_top / total_height)))

    def refresh_scoreboard(self) -> None:
        throw_limit = self.game_throw_limit()
        for player_idx, player in enumerate(self.players):
            self.score_labels[player_idx].config(text=str(player.score))
            for throw_idx, darts in enumerate(player.throws[:throw_limit]):
                row_values = [value for value in darts if value is not None]
                for dart_idx, value in enumerate(darts):
                    active = (
                        not self.match_over
                        and player_idx == self.current_player_idx
                        and throw_idx == self.current_throw_index(player)
                    )
                    completed = throw_idx < player.throw_count
                    bg = "#f7e4bb" if active else "#f1eadf" if completed else "#fffdf7"
                    self.throw_cells[(player_idx, throw_idx, dart_idx)].config(
                        text="" if value is None else str(value),
                        bg=bg,
                        cursor="hand2" if value is not None else "",
                    )

                sum_text = "" if not row_values else str(sum(row_values))
                if self.is_aimed_game() and row_values:
                    target = self.aimed_targets[throw_idx]
                    sum_text = f"{target}/{sum(row_values)}" if target is not None else str(sum(row_values))
                sum_bg = "#fff7e8"
                if throw_idx in player.bust_rows:
                    sum_text = "BUST"
                    sum_bg = "#e8a29a"
                elif row_values:
                    sum_bg = "#f7e4bb"
                self.sum_cells[(player_idx, throw_idx)].config(text=sum_text, bg=sum_bg)

            scores = self.player_dart_scores(player)
            self.draw_histogram(player_idx, scores)
            self.stats_labels[player_idx].config(text=self.format_player_stats(player))

        self.after_idle(self.scroll_to_current_input)

    def refresh_status(self) -> None:
        if self.match_over:
            if self.turn_label:
                self.turn_label.config(text="Game finished")
            if self.dart_label:
                self.dart_label.config(text="Start a new game to continue.")
            if self.throw_label:
                self.throw_label.config(text="Throws this turn: -")
            if self.next_turn_button:
                self.next_turn_button.config(state="disabled")
            return

        player = self.players[self.current_player_idx]
        throw_idx = self.current_throw_index(player)
        throw_limit = self.game_throw_limit()
        target = self.ensure_aimed_target(throw_idx)
        if self.turn_label:
            self.turn_label.config(text=f"Throwing: {player.name}")
        if self.dart_label:
            if self.is_aimed_game():
                target_text = f"Target: {target}" if target is not None else "Target: -"
                if self.pending_turn_complete:
                    text = f"Throw {throw_idx + 1}/{throw_limit} complete | {target_text} | Score: {player.score}"
                else:
                    text = (
                        f"Throw {throw_idx + 1}/{throw_limit} | "
                        f"Dart {self.dart_in_turn + 1}/{DARTS_PER_THROW} | {target_text} | Score: {player.score}"
                    )
            elif self.pending_turn_complete:
                text = f"Throw {throw_idx + 1}/{throw_limit} complete | Remaining: {player.score}"
            else:
                text = f"Throw {throw_idx + 1}/{throw_limit} | Dart {self.dart_in_turn + 1}/{DARTS_PER_THROW} | Remaining: {player.score}"
            self.dart_label.config(text=text)
        if self.throw_label:
            thrown = ", ".join(str(score) for score in self.turn_scores) if self.turn_scores else "-"
            self.throw_label.config(text=f"Throws this turn: {thrown}")
        if self.next_turn_button:
            self.next_turn_button.config(state="normal" if self.pending_turn_complete else "disabled")
        self.refresh_scoreboard()


if __name__ == "__main__":
    app = DartScoreApp()
    app.mainloop()
