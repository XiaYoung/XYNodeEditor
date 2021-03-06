import os
import sys
import inspect

from PySide2.QtWidgets import QApplication

from xynodeeditor.utils import loadStylesheet
from xynodeeditor.node_editor_window import NodeEditorWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)

    wnd = NodeEditorWindow()

    module_path = os.path.dirname(inspect.getfile(wnd.__class__))

    loadStylesheet(os.path.join(module_path, 'qss/nodestyle.qss'))

    sys.exit(app.exec_())
