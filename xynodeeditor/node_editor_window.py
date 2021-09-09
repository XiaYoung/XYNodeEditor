import os
import json

from PySide2.QtCore import QPoint, QSettings, QSize
from PySide2.QtWidgets import QAction, QApplication, QFileDialog, QLabel, QMainWindow, QMessageBox
from xynodeeditor.node_editor_widget import NodeEditorWidget


class NodeEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.name_company = 'Mathlovart'
        self.name_product = 'XYNodeEditor'

        self.initUI()

    def initUI(self):
        self.createActions()
        self.createMenus()

        # create node editor widget
        self.nodeeditor = NodeEditorWidget(self)
        self.nodeeditor.scene.addHasBeenModifiedListener(self.setTitle)
        self.setCentralWidget(self.nodeeditor)

        self.createStatusBar()

        # set window properties
        self.setGeometry(200, 200, 800, 600)

        self.setTitle()
        self.show()

    def createStatusBar(self):
        # status bar
        self.statusBar().showMessage("")
        self.status_mouse_pos = QLabel("")
        self.statusBar().addPermanentWidget(self.status_mouse_pos)
        # TODO:了解signal的用法
        self.nodeeditor.view.scenePosChangedSignal.connect(self.onScenePosChanged)

    def createActions(self):
        self.actNew = QAction('&New', self, shortcut='Ctrl+N',  statusTip='Creat new graph', triggered=self.onFileNew)
        self.actOpen = QAction('&Open', self, shortcut='Ctrl+O',  statusTip='Open file', triggered=self.onFileOpen)
        self.actSave = QAction('&Save', self, shortcut='Ctrl+S',  statusTip='Save file', triggered=self.onFileSave)
        self.actSaveAs = QAction('Save &As', self, shortcut='Ctrl+Shift+S',  statusTip='Save file as ...', triggered=self.onFileSaveAs)
        self.actExit = QAction('&Exit', self, shortcut='Ctrl+Q',  statusTip='Exit application', triggered=self.close)

        self.actUndo = QAction('&Undo', self, shortcut='Ctrl+Z',  statusTip='Undo last operation', triggered=self.onEditUndo)
        self.actRedo = QAction('&Redo', self, shortcut='Ctrl+Shift+Z',  statusTip='Redo last operation', triggered=self.onEditRedo)
        self.actCut = QAction('Cu&t', self, shortcut='Ctrl+X',  statusTip='Cut to clipboard', triggered=self.onEditCut)
        self.actCopy = QAction('&Copy', self, shortcut='Ctrl+C',  statusTip='Copy to clipboard', triggered=self.onEditCopy)
        self.actPast = QAction('&Paste', self, shortcut='Ctrl+V',  statusTip='Paste from clipboard', triggered=self.onEditPaste)
        self.actDelete = QAction('&Delete', self, shortcut='Del',  statusTip='Delete selected items', triggered=self.onEditDelete)

    def createMenus(self):
        # initialize munu
        menubar = self.menuBar()
        self.fileMenu = menubar.addMenu('&File')
        self.fileMenu.addAction(self.actNew)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.actOpen)
        self.fileMenu.addAction(self.actSave)
        self.fileMenu.addAction(self.actSaveAs)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.actExit)
        self.editMenu = menubar.addMenu('&Edit')
        self.editMenu.addAction(self.actUndo)
        self.editMenu.addAction(self.actRedo)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.actCut)
        self.editMenu.addAction(self.actCopy)
        self.editMenu.addAction(self.actPast)
        self.editMenu.addSeparator()
        self.editMenu.addAction(self.actDelete)

    def setTitle(self):
        title = "Node Editor - "
        title += self.getCurrentNodeEditorWidget().getUserFriendlyFilename()

        self.setWindowTitle(title)

    def closeEvent(self, event):
        if self.maybeSave():
            event.accept()
        else:
            event.ignore()

    def isModified(self):
        return self.getCurrentNodeEditorWidget().scene.has_been_modified

    def getCurrentNodeEditorWidget(self):
        return self.centralWidget()

    def maybeSave(self):
        if not self.isModified():
            return True

        res = QMessageBox.warning(
            self, "About to lose your work?",
            "The document has been modified.\n Do you want to save your changes?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

        if res == QMessageBox.Save:
            return self.onFileSave()
        elif res == QMessageBox.Cancel:
            return False

        return True

    def onScenePosChanged(self, x, y):
        self.status_mouse_pos.setText("Scene Pos:[%d, %d]" % (x, y))

    def onFileNew(self):
        if self.maybeSave():
            self.getCurrentNodeEditorWidget().scene.clear()
            self.getCurrentNodeEditorWidget().filename = None
            self.setTitle()

    def onFileOpen(self):
        if self.maybeSave():
            fname, filter = QFileDialog.getOpenFileName(
                self, 'Open graph from file')
            if fname == '':
                return
            if os.path.isfile(fname):
                self.getCurrentNodeEditorWidget().scene.loadFromFile(fname)
                self.getCurrentNodeEditorWidget().filename = fname
                self.setTitle()

    def onFileSave(self):
        if self.getCurrentNodeEditorWidget().filename is None:
            return self.onFileSaveAs()

        self.getCurrentNodeEditorWidget().scene.saveToFile(self.getCurrentNodeEditorWidget().filename)
        self.statusBar().showMessage("Successfull save %s" % self.getCurrentNodeEditorWidget().filename)
        self.setTitle()
        return True

    def onFileSaveAs(self):
        # print('On File Save As clicked!')
        fname, filter = QFileDialog.getSaveFileName(self, 'Save graph to file')
        if fname == '':
            return False
        self.getCurrentNodeEditorWidget().filename = fname
        self.onFileSave()
        return True

    def onEditUndo(self):
        self.getCurrentNodeEditorWidget().scene.history.undo()

    def onEditRedo(self):
        self.getCurrentNodeEditorWidget().scene.history.redo()

    def onEditDelete(self):
        self.getCurrentNodeEditorWidget().scene.grScene.views()[0].deleteSelected()

    def onEditCut(self):
        data = self.getCurrentNodeEditorWidget().scene.clipboard.serializeSelected(
            delete=True)
        str_data = json.dumps(data, indent=4)
        QApplication.instance().clipboard().setText(str_data)

    def onEditCopy(self):
        data = self.getCurrentNodeEditorWidget().scene.clipboard.serializeSelected(
            delete=False)
        str_data = json.dumps(data, indent=4)
        # print(str_data)
        QApplication.instance().clipboard().setText(str_data)

    def onEditPaste(self):
        raw_data = QApplication.instance().clipboard().text()
        try:
            data = json.loads(raw_data)
        except ValueError as e:
            print("Pasting of not valid json data!", e)
            return

        # check if the json data are correct
        if 'nodes' not in data:
            print("JSON does not contain any nodes!")
            return

        self.getCurrentNodeEditorWidget().scene.clipboard.deserializeFromClipboard(data)

    def readSettings(self):
        settings = QSettings(self.name_company, self.name_product)
        pos = settings.value('pos', QPoint(200, 200))
        size = settings.value('size', QSize(400, 400))

        self.move(pos)
        self.resize(size)

    def writeSettings(self):
        settings = QSettings(self.name_company, self.name_product)
        settings.setValue('pos', self.pos())
        settings.setValue('size', self.size())
