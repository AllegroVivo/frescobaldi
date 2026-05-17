# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2008 - 2014 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
Manages ActionCollections for a MainWindow (and so, effectively, for the whole
application.)

This makes it possible to edit actions and check whether keyboard shortcuts of
actions conflict with other actions.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Iterator, Tuple, Sequence
from weakref import WeakValueDictionary

from PySide6.QtGui import QKeySequence, QAction

import actioncollection
import plugin
import qutil

if TYPE_CHECKING:
    from .mainwindow import MainWindow
    from .actioncollection import ActionCollectionBase


def manager(mainwindow: MainWindow) -> ActionCollectionManager:
    """Returns the ActionCollectionManager belonging to mainwindow."""
    return ActionCollectionManager.instance(mainwindow)

def action(collection_name: str, action_name: str) -> Optional[QKeySequence]:
    """Return a QAction from the application.

    May return None, if the named collection or action does not exist.

    """
    for mgr in ActionCollectionManager.instances():
        return mgr.action(collection_name, action_name)


class ActionCollectionManager(plugin.MainWindowPlugin):
    """Manages ActionCollections for a MainWindow."""
    # noinspection PyMissingConstructor
    def __init__(self, _: MainWindow):
        """Creates the ActionCollectionManager for the given mainwindow."""
        self._actioncollections: WeakValueDictionary[str, ActionCollectionBase] = WeakValueDictionary()

    def addActionCollection(self, collection: ActionCollectionBase) -> None:
        """Add an actioncollection to our list (used for changing keyboard shortcuts).

        Does not keep a reference to it.  If the ActionCollection gets garbage collected,
        it is removed automatically from our list.

        """
        if collection.name not in self._actioncollections:
            self._actioncollections[collection.name] = collection

    def removeActionCollection(self, collection: ActionCollectionBase) -> None:
        """Removes the given ActionCollection from our list."""
        if collection.name in self._actioncollections:
            del self._actioncollections[collection.name]

    def actionCollections(self) -> Iterator[ActionCollectionBase]:
        """Iterate over the ActionCollections in our list."""
        return self._actioncollections.values()

    def action(self, collection_name: str, action_name: str):
        """Returns the named action from the named collection."""
        collection = self._actioncollections.get(collection_name)
        if collection:
            if isinstance(collection, actioncollection.ShortcutCollection):
                return collection.realAction(action_name)
            return getattr(collection, action_name, None)

    def iterShortcuts(
        self,
        skip: Optional[Tuple[ActionCollectionBase, str]] = None
    ) -> Iterator[Tuple[QKeySequence, ActionCollectionBase, str, QAction]]:
        """Iter all shortcuts of all collections."""
        for collection in self.actionCollections():
            for name, a in collection.actions().items():
                if (collection, name) != skip:
                    for shortcut in collection.shortcuts(name):  # type: ignore - SP
                        yield shortcut, collection, name, a

    def findShortcutConflict(
        self,
        shortcut: QKeySequence,
        skip: Tuple[ActionCollectionBase, str]
    ) -> Optional[str]:
        """Find the possible shortcut conflict and return the conflict name.

        skip must be a tuple (collection, name).
        it's the action to skip (the action that is about to be changed).

        """
        if shortcut:
            for data in self.iterShortcuts(skip):
                s1 = data[0]
                if isShortcutConflict(s1, shortcut):
                    return qutil.removeAccelerator(data[-1].text())
        return None

    def removeShortcuts(self, shortcuts: Sequence[QKeySequence]) -> None:
        """Find and remove shortcuts of the given list."""
        for data in self.iterShortcuts():
            s1, collection, name = data[:3]
            for s2 in shortcuts:
                if isShortcutConflict(s1, s2):
                    collShortcuts = collection.shortcuts(name)
                    collShortcuts.remove(s1)
                    collection.setShortcuts(name, collShortcuts)

def isShortcutConflict(s1: QKeySequence, s2: QKeySequence) -> bool:
    return (
        s1.matches(s2) != QKeySequence.SequenceMatch.NoMatch
        or s2.matches(s1) != QKeySequence.SequenceMatch.NoMatch
    )
