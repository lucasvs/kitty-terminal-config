import datetime
import json
import subprocess
from collections import defaultdict

from kitty.boss import get_boss
from kitty.fast_data_types import Screen, add_timer, get_options
from kitty.utils import color_as_int
from kitty.tab_bar import (
    DrawData,
    ExtraData,
    Formatter,
    TabBarData,
    as_rgb,
    draw_attributed_string,
    draw_tab_with_powerline,
)

timer_id = None

opts = get_options()

KUBE_FG = 0
KUBE_BG = as_rgb(color_as_int(opts.color6))
TAB_BG = as_rgb(color_as_int(opts.color6))
REFRESH_TIME = 1

def _redraw_tab_bar(timer_id):
    tm = get_boss().active_tab_manager
    if tm is not None:
        tm.mark_tab_bar_dirty()

def draw_tab(
    draw_data: DrawData,
    screen: Screen,
    tab: TabBarData,
    before: int,
    max_title_length: int,
    index: int,
    is_last: bool,
    extra_data: ExtraData,
) -> int:
    global timer_id

    if timer_id is None:
         timer_id = add_timer(_redraw_tab_bar, REFRESH_TIME, True)
    draw_tab_with_powerline(
        draw_data, screen, tab, before, max_title_length, index, is_last, extra_data
    )
    if is_last:
        draw_right_status(draw_data, screen)
    return screen.cursor.x

def draw_right_status(draw_data: DrawData, screen: Screen) -> None:
    # The tabs may have left some formats enabled. Disable them now.
    draw_attributed_string(Formatter.reset, screen)
    cells = create_cells()
    # Drop cells that wont fit
    while True:
        if not cells:
            return
        padding = screen.columns - screen.cursor.x - sum(len(c) + 3 for c in cells)
        if padding >= 0:
            break
        cells = cells[1:]

    if padding:
        screen.draw(" " * padding)

    tab_bg = as_rgb(int(draw_data.inactive_bg))
    tab_fg = as_rgb(int(draw_data.inactive_fg))
    default_bg = as_rgb(int(draw_data.default_bg))
    for cell in cells:
        # Draw the separator
        if cell == cells[0]:
            screen.cursor.fg = KUBE_BG
            screen.draw("")
        else:
            screen.cursor.fg = default_bg
            screen.cursor.bg = tab_bg
            screen.draw("")
        screen.cursor.fg = tab_fg
        screen.cursor.bg = KUBE_BG
        screen.draw(f" {cell} ")


def create_cells() -> list[str]:
    now = datetime.datetime.now()
    return [
        get_kube_context_status(),
        #now.strftime("%d %b"),
        #now.strftime("%H:%M"),
    ]


def get_kube_context_status():
    try:
        context = subprocess.getoutput('awk "/^current-context:/{print $2;exit;}" <~/.kube/config | cut -d "_" -f 4')
    except Exception:
        context = ""

    return f"{context}"
