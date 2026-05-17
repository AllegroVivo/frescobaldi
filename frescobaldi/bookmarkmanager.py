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
Manages the actions that manipulate the bookmarks (see also bookmarks.py).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QWidget

import actioncollection
import actioncollectionmanager
import icons
import bookmarks
import plugin

if TYPE_CHECKING:
    from .mainwindow import MainWindow
    from .view import View
    from .document import Document


class BookmarkManager(plugin.MainWindowPlugin):
    # noinspection PyMissingConstructor
    def __init__(self, mainwindow: MainWindow):
        self.actionCollection: Actions = Actions()
        ac = self.actionCollection
        actioncollectionmanager.manager(mainwindow).addActionCollection(ac)
        ac.view_next_mark.triggered.connect(self.nextMark)
        ac.view_previous_mark.triggered.connect(self.previousMark)
        ac.view_bookmark.triggered.connect(self.markCurrentLine)
        ac.view_clear_error_marks.triggered.connect(self.clearErrorMarks)
        ac.view_clear_all_marks.triggered.connect(self.clearAllMarks)
        mainwindow.currentViewChanged.connect(self.slotViewChanged)
        mainwindow.currentDocumentChanged.connect(self.slotDocumentChanged)
        if mainwindow.currentView():
            self.slotViewChanged(mainwindow.currentView())
            self.slotDocumentChanged(mainwindow.currentDocument())

    def slotViewChanged(self, view: View, prev: Optional[View] = None) -> None:
        if prev:
            prev.cursorPositionChanged.disconnect(self.updateMarkStatus)
        view.cursorPositionChanged.connect(self.updateMarkStatus)

    def slotDocumentChanged(self, doc: Document, prev: Optional[Document] = None) -> None:
        if prev:
            bookmarks.bookmarks(prev).marksChanged.disconnect(self.updateMarkStatus)
        bookmarks.bookmarks(doc).marksChanged.connect(self.updateMarkStatus)

    def updateMarkStatus(self) -> None:
        view = self.mainwindow().currentView()
        self.actionCollection.view_bookmark.setChecked(
            bookmarks.bookmarks(view.document()).hasMark(view.textCursor().blockNumber(), 'mark'))

    def markCurrentLine(self) -> None:
        view = self.mainwindow().currentView()
        lineNumber = view.textCursor().blockNumber()
        bookmarks.bookmarks(view.document()).toggleMark(lineNumber, 'mark')

    def clearErrorMarks(self) -> None:
        doc = self.mainwindow().currentDocument()
        bookmarks.bookmarks(doc).clear('error')

    def clearAllMarks(self) -> None:
        doc = self.mainwindow().currentDocument()
        bookmarks.bookmarks(doc).clear()

    def nextMark(self) -> None:
        view = self.mainwindow().currentView()
        cursor = view.textCursor()
        cursor = bookmarks.bookmarks(view.document()).nextMark(cursor)
        if cursor:
            view.gotoTextCursor(cursor)

    def previousMark(self) -> None:
        view = self.mainwindow().currentView()
        cursor = view.textCursor()
        cursor = bookmarks.bookmarks(view.document()).previousMark(cursor)
        if cursor:
            view.gotoTextCursor(cursor)


class Actions(actioncollection.ActionCollection):
    name = "bookmarkmanager"

    def createActions(self, parent: Optional[QWidget] = None) -> None:
        self.view_bookmark = QAction(parent)
        self.view_bookmark.setCheckable(True)
        self.view_clear_error_marks = QAction(parent)
        self.view_clear_all_marks = QAction(parent)
        self.view_next_mark = QAction(parent)
        self.view_previous_mark = QAction(parent)

        self.view_bookmark.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_B))
        self.view_next_mark.setShortcut(QKeySequence(Qt.Modifier.ALT | Qt.Key.Key_PageDown))
        self.view_previous_mark.setShortcut(QKeySequence(Qt.Modifier.ALT | Qt.Key.Key_PageUp))

        self.view_bookmark.setIcon(icons.get('bookmark-new'))
        self.view_clear_all_marks.setIcon(icons.get('edit-clear'))

    def translateUI(self) -> None:
        self.view_bookmark.setText(_("&Mark Current Line"))
        self.view_clear_error_marks.setText(_("Clear &Error Marks"))
        self.view_clear_all_marks.setText(_("Clear &All Marks"))
        self.view_next_mark.setText(_("Next Mark"))
        self.view_previous_mark.setText(_("Previous Mark"))
