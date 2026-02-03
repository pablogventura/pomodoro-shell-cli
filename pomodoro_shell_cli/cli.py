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
import sys

import dbus
import dbus.mainloop.glib
from gi.repository import GLib
from math import floor, ceil


SERVICE_NAME = 'org.gnome.Pomodoro'
OBJECT_PATH = '/org/gnome/Pomodoro'
INTERFACE_NAME = 'org.gnome.Pomodoro'

properties_interface = None


def format_time(seconds):
    hours = seconds // 3600;
    minutes = (seconds % 3600) // 60;
    parts = []

    seconds = seconds % 60;

    if hours > 0:
        parts.append(f'{hours}h');

    if minutes > 0:
        parts.append(f'{minutes}m');

    if hours == 0:
        parts.append(f'{seconds}s');

    return ' '.join(parts)


def print_timer_state():
    global properties_interface
    
    data = properties_interface.GetAll(INTERFACE_NAME)

    elapsed = floor(data['Elapsed'])
    remaining = ceil(data['StateDuration'] - elapsed)
    is_paused = data['IsPaused']
    state = data['State']

    if is_paused and elapsed == 0 and state == 'pomodoro':
        print(f'Break Over!')
        return

    if is_paused:
        remaining_string = 'Paused'
    else:
        remaining_string = format_time(remaining)

    match state:
        case 'pomodoro':
            print(f'Pomodoro {remaining_string}')

        case 'short-break':
            print(f'Break {remaining_string}')

        case 'long-break':
            print(f'Break {remaining_string}')

        case _:
            print('Stopped')


def get_pomodoro_interface():
    """Obtiene la interfaz de control de GNOME Pomodoro."""
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    proxy = bus.get_object(SERVICE_NAME, OBJECT_PATH)
    return dbus.Interface(proxy, INTERFACE_NAME)


def run_command(command: str) -> bool:
    """Ejecuta un comando y retorna True si tuvo éxito."""
    try:
        iface = get_pomodoro_interface()
        if command == 'start':
            iface.Start()
        elif command == 'stop':
            iface.Stop()
        elif command == 'pause':
            iface.Pause()
        elif command == 'resume':
            iface.Resume()
        elif command == 'skip':
            iface.Skip()
        elif command == 'reset':
            iface.Reset()
        else:
            return False
        return True
    except dbus.exceptions.DBusException as e:
        print(f'Error: {e}', file=sys.stderr)
        return False


def on_properties_changed(interface, changed, invalidated):
    """
    Callback for when a property changes.
    Args:
        - interface: The interface of the property.
        - changed: A dictionary of changed properties.
        - invalidated: A list of invalidated properties.
        - path: Object path of the change.
    """
    print_timer_state()


def main():
    global properties_interface

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
            dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
            bus = dbus.SessionBus()
            proxy_object = bus.get_object(SERVICE_NAME, OBJECT_PATH)
            properties_interface = dbus.Interface(proxy_object, 'org.freedesktop.DBus.Properties')
            print_timer_state()
        else:
            if run_command(args.command):
                print(f'OK: {args.command}')
            else:
                sys.exit(1)
        return

    # Modo watch: mostrar estado y escuchar cambios
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SessionBus()
    proxy_object = bus.get_object(SERVICE_NAME, OBJECT_PATH)
    properties_interface = dbus.Interface(proxy_object, 'org.freedesktop.DBus.Properties')
    properties_interface.connect_to_signal('PropertiesChanged', on_properties_changed)

    print_timer_state()

    loop = GLib.MainLoop()
    loop.run()


if __name__ == '__main__':
    main()
