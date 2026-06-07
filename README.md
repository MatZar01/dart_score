# dart_score

`dart_score` is a desktop darts scoring application for simple one-leg `301`, `501`, and `Aimed` games. It is designed for local manual scoring: enter player names, choose the game, then click the dartboard segments as each dart is thrown.

The app uses a left-side scoreboard and a right-side clickable dartboard. `301` and `501` do not require double-out; a player wins as soon as their score reaches exactly zero.

## Features

- Setup screen for entering player names.
- Game selection for `301`, `501`, or `Aimed`.
- One-leg game format.
- Up to 15 three-dart throws per player in `301` and `501`; 10 in `Aimed`.
- Clickable dartboard with singles, doubles, triples, bull `25`, bullseye `50`, and `Miss / 0`.
- `Aimed` mode rolls one random target from `1` to `20` for each throw row; every player aims at the same target for that row.
- Stationary scoreboard header with player names, total scores, and `Throw / D1 / D2 / D3 / Sum` labels. In `Aimed`, the last column shows `Target/Sum`.
- Scrollable throw table that auto-scrolls to keep the current player's input area visible.
- Per-player statistics with a horizontally scrollable stats area.
- Histogram bar chart, mean, median, and population standard deviation for each player's dart scores.
- Click-to-edit dart scores directly in the scoreboard.
- Explicit `Next turn` button after a player finishes a turn.
- Bust handling when a `301` or `501` throw takes the score below zero.

## Libraries

No third-party libraries are required.

Required runtime components:

- Python 3
- `tkinter` / Tk, included in the current `dart` conda environment

Verified in this environment with Python 3.13 and Tk 8.6.

## How To Use

1. Start the app.
2. Enter at least two player names, one per line.
3. Select `501`, `301`, or `Aimed`.
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

- In `301` and `501`, each player starts from the selected game score.
- Each turn contains up to three darts.
- Exact zero wins the game immediately.
- Double-out is not required.
- If a dart makes the score go below zero, the turn is a bust.
- On bust, the player's score returns to the value from the start of that turn.
- Bust rows are marked as `BUST` in the `Sum` column.
- If all players use 15 throw rows in `301` or `501` without reaching zero, the player with the lowest remaining score wins.
- In `Aimed`, each player starts at `0`.
- In `Aimed`, each throw row gets one random target number from `1` to `20`, shared by all players.
- In `Aimed`, only singles, doubles, and triples of the target number score; all other fields, bull `25`, bullseye `50`, and misses score `0`.
- In `Aimed`, the player with the highest score after 10 turns wins.

## Statistics

Each player has a statistics card below the scoreboard:

- Histogram: bar chart of individual dart scores.
- Mean: average individual dart score.
- Median: median individual dart score.
- Std dev: population standard deviation of individual dart scores.

Misses count as `0`. Empty future dart cells are ignored.
