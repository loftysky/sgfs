from __future__ import absolute_import

import functools
import sys
from subprocess import call
import os

import nuke

from sgfs import SGFS
from uitools.qt import QtGui

from .utils import dispatch


_menu_bar = nuke.menu('Nuke')
_sgfs = SGFS()


_entity_icons = {
    'Sequence': 'fatcow/film_link',
    'Shot': 'fatcow/film',
    'PublishEvent': 'fatcow/brick',
    'Asset': 'fatcow/box_closed',
    'Version': 'fatcow/images',
    'Project': 'fatcow/newspaper',
    'Task': 'fatcow/tick',
}

_entity_name_formats = {
    'Project': '{name}',
    'Asset': '{code}',
    'Sequence': '{code}',
    'Shot': '{code}',
    'Task': '{entity[code]} - {step[code]}',
}


def _icon_path(name):
    if not name:
        return
    return os.path.abspath(os.path.join(__file__, 
            '..', '..', '..',
            'icons', name + '.png'
    ))

def _clear_existing():
    for i, item in enumerate(_menu_bar.items()):
        if item.name().startswith('Shotgun'):
            _menu_bar.removeItem(item.name())
            return i





def _open_entity(entity):

    main_window = [x 
        for x in QtGui.QApplication.instance().topLevelWidgets()
        if isinstance(x, QtGui.QMainWindow)
    ][0]

    msgbox = QtGui.QMessageBox(main_window)
    msgbox.setText('Where would you like to go?')

    shotgun = msgbox.addButton(
        "Shotgun",
        msgbox.AcceptRole,
    )
    finder = msgbox.addButton(
        "Finder" if sys.platform == 'darwin' else 'File Browser',
        msgbox.AcceptRole,
    )
    
    msgbox.addButton(msgbox.Cancel)

    msgbox.setDefaultButton(shotgun)
    msgbox.exec_()

    if msgbox.clickedButton() is shotgun:
        dest = entity.url
    elif msgbox.clickedButton() is finder:
        dest = _sgfs.path_for_entity(entity)
    else:
        dest = None

    if dest:
        call(['open' if sys.platform == 'darwin' else 'xdg-open', dest])


def build_for_path(path):

    entities = _sgfs.entities_from_path(path)

    # Pick a nice name.
    if entities:
        entity = entities[0]
        menu_name_pattern = _entity_name_formats.get(entity['type'], '{type}')
        menu_name = 'Shotgun [%s]' % menu_name_pattern.format(**entity)
    else:
        menu_name = 'Shotgun [detached]'
        entity = None

    # Append or insert the menu if it existed.
    index = _clear_existing()
    if index is not None:
        menu = _menu_bar.addMenu(menu_name, index=index)
    else:
        menu = _menu_bar.addMenu(menu_name)

    if entity:
        # Generate an item for every step up to the top.
        head = entity
        while head and head['type'] in _entity_name_formats:
            menu.addCommand(
                'Go to %s' % _entity_name_formats[head['type']].format(**head),
                functools.partial(_open_entity, head),
                icon=_icon_path(_entity_icons.get(head['type'])),
            )
            head = head.parent()
    else:
        menu.addCommand('No entities found!').setEnabled(False)

    menu.addSeparator()

    menu.addCommand(
        'Open from Work Area...',
        functools.partial(dispatch, 'sgfs.nuke.open_script:run'),
        'ctrl+alt+O',
    )
    menu.addCommand(
        'Save to Work Area...',
        functools.partial(dispatch, 'sgfs.nuke.save_script:run'),
        'ctrl+alt+S',
    )

    if 'KS_DEV_ARGS' in os.environ:
        menu.addSeparator()
        menu.addCommand(
            '[dev] Reload',
            functools.partial(dispatch, '%s:build_for_path' % __name__, (path, )),
        )



