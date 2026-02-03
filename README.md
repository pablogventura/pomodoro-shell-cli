# Pomodoro Shell CLI

A command-line interface (CLI) for [GNOME Pomodoro](https://gnomepomodoro.org/). Control your pomodoro timer from the terminal—start, pause, skip, or stop sessions without opening the app.

## What is it?

Pomodoro Shell CLI connects to GNOME Pomodoro via D-Bus and lets you:

- **Check status** — See the current timer state (pomodoro, short break, long break) and remaining time
- **Control the timer** — Start, stop, pause, resume, or skip sessions from the command line
- **Watch mode** — Run without arguments to display the state and auto-update when it changes

Useful for custom workflows, keyboard shortcuts, status bars (e.g. Waybar), or scripting.

## Installation

### With pipx (recommended)

[pipx](https://pypa.github.io/pipx/) installs the tool in an isolated environment and makes the `pomodoro` command available globally. No system build dependencies required — the package uses pure Python D-Bus bindings.

```bash
pipx install .
```

From a Git repository:

```bash
pipx install git+https://github.com/pablogventura/pomodoro-shell-cli.git
```

### From source

```bash
pip install -e .
```

Or run without installing (requires `pip install dbus-fast` first):

```bash
python -m pomodoro_shell_cli start
```

## Requirements

- Python 3.10+
- [GNOME Pomodoro](https://gnomepomodoro.org/) running (or available on your session)

**Runtime**: [GNOME Pomodoro](https://gnomepomodoro.org/) must be installed and running. On systems with GNOME, D-Bus and GLib are typically already available.

## Usage

```bash
pomodoro [command]
```

| Command | Description |
|---------|-------------|
| *(none)* | Watch mode: show state and listen for changes |
| `status` | Show current state once and exit |
| `start` | Start a pomodoro |
| `stop` | Stop the timer |
| `pause` | Pause current session |
| `resume` | Resume paused session |
| `skip` | Skip to next (break or pomodoro) |
| `reset` | Reset current timer |

### Examples

```bash
# Start a pomodoro
pomodoro start

# Pause it
pomodoro pause

# Skip to the break
pomodoro skip

# Check status
pomodoro status

# Run in watch mode (updates on every change)
pomodoro
```

## License

MIT
