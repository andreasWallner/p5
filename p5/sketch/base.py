#
# Part of p5: A Python package based on Processing
# Copyright (C) 2017 Abhik Pal
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""Base module for a sketch."""

import __main__
import builtins
from functools import wraps

import pyglet
pyglet.options["shadow_window"] = False

from ..opengl import renderer

__all__ = ['setup', 'draw', 'run', 'no_loop', 'loop', 'redraw', 'size',
           'title', 'no_cursor', 'cursor', 'exit', 'set_frame_rate']

builtins.width = 200
builtins.height = 200
builtins.title = "p5"
builtins.frame_count = -1
builtins.frame_rate = 30

builtins.pixel_width = 1
builtins.pixel_height = 1

platform = pyglet.window.get_platform()
display = platform.get_default_display()
screen = display.get_default_screen()

template = pyglet.gl.Config(samples_buffers=1, samples=2)
try:
    config = screen.get_best_config(template)
except pyglet.window.NoSuchConfigException:
    template = pyglet.gl.Config()
    config = screen.get_best_config(template)

window = pyglet.window.Window(
    width=builtins.width,
    height=builtins.height,
    caption=builtins.title,
    resizable=False,
    visible=False,
    vsync=False,
    config=config
)

window.set_minimum_size(100, 100)

# DO NOT REMOVE THIS
#
# We tried removing this line and things broke badly on Mac machines.
# We still don't know why. Let's just keep this here for now.
_ = pyglet.clock.ClockDisplay()

def _dummy_handler(*args, **kwargs):
    return pyglet.event.EVENT_HANDLED

handler_names = [ 'key_press', 'key_pressed', 'key_released',
                  'key_typed', 'mouse_clicked', 'mouse_dragged',
                  'mouse_moved', 'mouse_pressed', 'mouse_released',
                  'mouse_wheel',]

handlers =  dict.fromkeys(handler_names, _dummy_handler)

handler_queue = []

looping = True
redraw = False
setup_done = False
target_frame_rate = 60.0
time_since_last_frame = 0.0

def draw():
    """Continuously execute code defined inside.

    The `draw()` function is called directly after `setup()` and all
    code inside is continuously executed until the program is stopped
    (using `exit()`) or `no_loop()` is called.

    """
    pass

def setup():
    """Called to setup initial sketch options.

    The `setup()` function is run once when the program starts and is
    used to define initial environment options for the sketch.

    """
    pass

def no_loop():
    """Stop draw() from being continuously called.

    By default, the sketch continuously calls `draw()` as long as it
    runs. Calling `no_loop()` stops draw() from being called the next
    time. Note that this only prevents execution of the code inside
    `draw()` and the user can manipulate the screen contents through
    event handlers like `mouse_pressed()`, etc.

    """
    global looping
    looping = False

def loop():
    """Make sure `draw()` is being called continuously.

    `loop()` reverts the effects of `no_loop()` and allows `draw()` to
    be called continously again.

    """
    global looping
    looping = True

def redraw():
    """Call `draw()` once.

    If looping has been disabled using `no_loop()`, `redraw()` will
    make sure that `draw()` is called *exactly* once.

    """
    global redraw
    if not looping:
        redraw = True

def size(width, height):
    """Resize the sketch window.

    :param width: width of the sketch window.
    :type width: int

    :param height: height of the sketch window.
    :type height: int

    """
    builtins.width = int(width)
    builtins.height = int(height)
    window.set_size(width, height)

def title(new_title):
    """Set the title of the p5 window.

    :param new_title: new title of the window.
    :type new_title: str

    """
    builtins.title = new_title
    window.set_caption(str(new_title))

def no_cursor():
    """Hide the mouse cursor.
    """
    window.set_mouse_visible(False)

def cursor(cursor_type='ARROW'):
    """Set the cursor to the specified type.

    :param cursor_type: The cursor type to be used (defaults to
        'ARROW'). Should be one of: {'ARROW','CROSS','HAND', 'MOVE',
        'TEXT', 'WAIT'}
    :type cursor_type: str

    """
    cursor_map = {
        'ARROW': window.CURSOR_DEFAULT,
        'CROSS': window.CURSOR_CROSSHAIR,
        'HAND': window.CURSOR_HAND,
        'MOVE': window.CURSOR_SIZE,
        'TEXT': window.CURSOR_TEXT,
        'WAIT': window.CURSOR_WAIT
    }
    selected_cursor = cursor_map.get(cursor_type, 'ARROW')
    cursor = window.get_system_mouse_cursor(selected_cursor)
    window.set_mouse_visible(True)
    window.set_mouse_cursor(cursor)

def exit(*args, **kwargs):
    """Exit the sketch.

    `exit()` overrides Python's builtin exit() function and makes sure
    that necessary cleanup steps are performed before exiting the
    sketch.

    :param args: positional argumets to pass to Python's builtin
        `exit()` function.

    :param kwargs: keyword-arguments to pass to Python's builtin
        `exit()` function.

    """
    pyglet.app.exit()
    builtins.exit(*args, **kwargs)

@window.event
def on_draw():
    pass

def update(dt):
    global handler_queue
    global redraw
    global setup_done
    global time_since_last_frame

    builtins.frame_rate = int(1 / (dt + 0.0001))
    time_since_last_frame += dt
    correct_frame_rate = time_since_last_frame > (1.0 / target_frame_rate)

    renderer.pre_render()
    if not setup_done:
        builtins.frame_count += 1
        setup()
        setup_done = True
    elif correct_frame_rate or builtins.frame_count == 0:
        if looping or redraw:
            builtins.frame_count += 1
            draw()
            redraw = False
        for function, event in handler_queue:
            function(event)
        handler_queue = []
        time_since_last_frame = 0

    renderer.post_render()

def initialize(*args, **kwargs):
    renderer.initialize(window.context)
    window.set_visible()

def set_frame_rate(fm):
    global target_frame_rate
    target_frame_rate = max(1, int(fm))

def fix_handler_interface(func):
    """Make sure that `func` takes at least one argument as input.

    :returns: a new function that accepts arguments.
    :rtype: func
    """
    @wraps(func)
    def fixed_func(*args, **kwargs):
        return_value = func()
        return return_value

    if func.__code__.co_argcount == 0:
        return fixed_func
    else:
        return func

def run(setup_func=None, draw_func=None):
    """Run a sketch.

    if no `setup_func` and `draw_func` are specified, p5 automatically
    "finds" the user-defined setup and draw functions.

    :param setup_func: The setup function of the sketch (None by
         default.)
    :type setup_func: function

    :param draw_func: The draw function of the sketch (None by
        default.)
    :type draw_func: function

    """
    global draw
    global setup

    if setup_func is not None:
        setup = setup_func
    elif hasattr(__main__, 'setup'):
        setup = __main__.setup

    if draw_func is not None:
        draw = draw_func
    elif hasattr(__main__, 'draw'):
        draw = __main__.draw

    for handler in handler_names:
        if hasattr(__main__, handler):
            handler_func = getattr(__main__, handler)
            handlers[handler] = fix_handler_interface(handler_func)

    initialize()
    pyglet.clock.schedule_interval(update, 1/(target_frame_rate + 1))
    pyglet.app.run()

def artist(f):
    # a decorator that will wrap around the the "artists" in the
    # sketch -- these are functions that draw stuff on the screen like
    # rect(), line(), etc.
    #
    #    @artist
    #    def rect(*args, **kwargs):
    #        # code that creates a rectangular Shape object and
    #        # returns it.
    @wraps(f)
    def decorated(*args, **kwargs):
        shape = f(*args, **kwargs)
        renderer.render(shape)
        return shape
    return decorated
