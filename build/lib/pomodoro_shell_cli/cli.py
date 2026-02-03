#!/usr/bin/env python
# Pomodoro Shell CLI
#
# Usage:
#   pomodoro              # Watch mode: show state and listen for changes
#   pomodoro status       # Show current state once and exit
#   pomodoro start        # Start a pomodoro
#   pomodoro stop         # Stop the timer
#   pomodoro pause        # Pause current session
#   pomodoro resume       # Resume paused session
#   pomodoro skip         # Skip to next (break or pomodoro)
#   pomodoro reset        # Reset current timer

import argparse
import asyncio
import sys

from dbus_fast.aio import MessageBus
from dbus_fast import Message, MessageType
from math import floor, ceil


SERVICE_NAME = 'org.gnome.Pomodoro'
OBJECT_PATH = '/org/gnome/Pomodoro'
INTERFACE_NAME = 'org.gnome.Pomodoro'
PROPERTIES_INTERFACE = 'org.freedesktop.DBus.Properties'

PROPERTIES_CHANGED_MATCH = (
    f"type='signal',interface='{PROPERTIES_INTERFACE}',"
    f"member='PropertiesChanged',path='{OBJECT_PATH}'"
)


def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    seconds = seconds % 60
    if hours > 0:
        parts.append(f'{hours}h')
    if minutes > 0:
        parts.append(f'{minutes}m')
    if hours == 0:
        parts.append(f'{seconds}s')
    return ' '.join(parts)


def _unwrap_variant(val):
    return val.value if hasattr(val, 'value') else val


def parse_timer_state(data):
    """Parse GetAll result into state dict."""
    result = {}
    for k, v in data.items():
        result[k] = _unwrap_variant(v)
    return result


def print_state_from_data(data):
    """Print timer state from properties dict."""
    elapsed = floor(data.get('Elapsed', 0) or 0)
    state_duration = data.get('StateDuration') or 0
    remaining = ceil(state_duration - elapsed)
    is_paused = data.get('IsPaused', False)
    state = data.get('State') or 'null'

    if is_paused and elapsed == 0 and state == 'pomodoro':
        print('Break Over!')
        return

    if is_paused:
        remaining_string = 'Paused'
    else:
        remaining_string = format_time(int(remaining))

    match state:
        case 'pomodoro':
            print(f'Pomodoro {remaining_string}')
        case 'short-break':
            print(f'Break {remaining_string}')
        case 'long-break':
            print(f'Break {remaining_string}')
        case _:
            print('Stopped')


async def get_properties(bus):
    """Get all Pomodoro properties via D-Bus."""
    msg = Message(
        destination=SERVICE_NAME,
        path=OBJECT_PATH,
        interface=PROPERTIES_INTERFACE,
        member='GetAll',
        signature='s',
        body=[INTERFACE_NAME],
    )
    reply = await bus.call(msg)
    if reply.message_type == MessageType.ERROR:
        raise Exception(reply.body[0] if reply.body else 'Unknown error')
    return parse_timer_state(reply.body[0])


async def call_pomodoro_method(bus, method: str):
    """Call a method on org.gnome.Pomodoro."""
    msg = Message(
        destination=SERVICE_NAME,
        path=OBJECT_PATH,
        interface=INTERFACE_NAME,
        member=method,
        signature='',
        body=[],
    )
    reply = await bus.call(msg)
    if reply.message_type == MessageType.ERROR:
        raise Exception(reply.body[0] if reply.body else 'Unknown error')


async def run_command_async(command: str) -> bool:
    """Execute a command and return True on success."""
    try:
        bus = MessageBus()
        await bus.connect()
        if command == 'start':
            await call_pomodoro_method(bus, 'Start')
        elif command == 'stop':
            await call_pomodoro_method(bus, 'Stop')
        elif command == 'pause':
            await call_pomodoro_method(bus, 'Pause')
        elif command == 'resume':
            await call_pomodoro_method(bus, 'Resume')
        elif command == 'skip':
            await call_pomodoro_method(bus, 'Skip')
        elif command == 'reset':
            await call_pomodoro_method(bus, 'Reset')
        else:
            return False
        bus.disconnect()
        return True
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        return False


def run_command(command: str) -> bool:
    """Execute a command (sync wrapper)."""
    return asyncio.run(run_command_async(command))


async def status_async():
    """Print current status once."""
    bus = MessageBus()
    await bus.connect()
    try:
        data = await get_properties(bus)
        print_state_from_data(data)
    finally:
        bus.disconnect()


async def watch_async():
    """Watch mode: print state and update on changes."""
    bus = MessageBus()
    await bus.connect()

    # Add match for PropertiesChanged
    add_match_msg = Message(
        destination='org.freedesktop.DBus',
        path='/org/freedesktop/DBus',
        interface='org.freedesktop.DBus',
        member='AddMatch',
        signature='s',
        body=[PROPERTIES_CHANGED_MATCH],
    )
    await bus.call(add_match_msg)

    # Print initial state
    data = await get_properties(bus)
    print_state_from_data(data)

    loop = asyncio.get_event_loop()
    update_event = asyncio.Event()

    def message_handler(msg):
        if (msg.message_type == MessageType.SIGNAL and
                msg.interface == PROPERTIES_INTERFACE and
                msg.member == 'PropertiesChanged' and
                msg.path == OBJECT_PATH):
            loop.call_soon(update_event.set)
        return None

    bus.add_message_handler(message_handler)

    async def watch_loop():
        while True:
            await update_event.wait()
            update_event.clear()
            try:
                data = await get_properties(bus)
                print_state_from_data(data)
            except Exception:
                pass

    watch_task = asyncio.create_task(watch_loop())

    try:
        await asyncio.Future()  # Run forever
    except asyncio.CancelledError:
        pass
    finally:
        watch_task.cancel()
        try:
            await watch_task
        except asyncio.CancelledError:
            pass
        bus.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description='CLI para GNOME Pomodoro. Sin argumentos, muestra el estado en tiempo real.'
    )
    parser.add_argument(
        'command',
        nargs='?',
        choices=['start', 'stop', 'pause', 'resume', 'skip', 'reset', 'status'],
        help='Comando a ejecutar: start, stop, pause, resume, skip, reset, status'
    )
    args = parser.parse_args()

    if args.command:
        if args.command == 'status':
            asyncio.run(status_async())
        else:
            if run_command(args.command):
                print(f'OK: {args.command}')
            else:
                sys.exit(1)
        return

    # Watch mode
    try:
        asyncio.run(watch_async())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
