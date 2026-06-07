# dart_score

`dart_score` is a desktop darts scoring application for simple one-leg `301` and `501` games. It is designed for local manual scoring: enter player names, choose the starting score, then click the dartboard segments as each dart is thrown.

The app uses a left-side scoreboard and a right-side clickable dartboard. It does not require double-out; a player wins as soon as their score reaches exactly zero.

## Features

- Setup screen for entering player names.
- Game selection for `301` or `501`.
- One-leg game format.
- Up to 15 three-dart throws per player.
- Clickable dartboard with singles, doubles, triples, bull `25`, bullseye `50`, and `Miss / 0`.
- Stationary scoreboard header with player names, total scores, and `Throw / D1 / D2 / D3 / Sum` labels.
- Scrollable throw table that auto-scrolls to keep the current player's input area visible.
- Per-player statistics with a horizontally scrollable stats area.
- Histogram bar chart, mean, median, and population standard deviation for each player's dart scores.
- Click-to-edit dart scores directly in the scoreboard.
- Explicit `Next turn` button after a player finishes a turn.
- Bust handling when a throw takes the score below zero.

## Run

```bash
conda activate dart
python app.py
```

Or without activating first:

```bash
conda run -n dart python app.py
```

## Libraries

No third-party libraries are required.

Required runtime components:

- Python 3
- `tkinter` / Tk, included in the current `dart` conda environment

Verified in this environment with Python 3.13 and Tk 8.6.

## How To Use

1. Start the app.
2. Enter at least two player names, one per line.
3. Select `501` or `301`.
4. Click `Start Game`.
5. For each dart, click the matching dartboard segment or click `Miss / 0`.
6. After three darts, click `Next turn` to switch to the next player.
7. Click an existing dart score in the scoreboard to edit it manually.
8. Use `New Game` to return to setup.

## Scoreboard Layout

The scoreboard is organized by throw number.

```text
          Player 1                  Player 2                  ...
          Total score               Total score
Throw     D1 | D2 | D3 | Sum        D1 | D2 | D3 | Sum
1
2
...
15
```

The header stays fixed while the throw rows scroll. When the current input moves down the table, the scoreboard auto-scrolls so a block of four throw rows remains visible where possible.

## Scoring Rules

- Each player starts from the selected game score: `301` or `501`.
- Each turn contains up to three darts.
- Exact zero wins the game immediately.
- Double-out is not required.
- If a dart makes the score go below zero, the turn is a bust.
- On bust, the player's score returns to the value from the start of that turn.
- Bust rows are marked as `BUST` in the `Sum` column.
- If all players use 15 throw rows without reaching zero, the player with the lowest remaining score wins.

## Statistics

Each player has a statistics card below the scoreboard:

- Histogram: bar chart of individual dart scores.
- Mean: average individual dart score.
- Median: median individual dart score.
- Std dev: population standard deviation of individual dart scores.

Misses count as `0`. Empty future dart cells are ignored.
