import sys
# sys.path.append('c:/Users/XiaYoung/codes/XYNodeEditor')

from PySide2.QtWidgets import QApplication
from xynodeeditor.node_editor_window import NodeEditorWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)

    wnd = NodeEditorWindow()

    sys.exit(app.exec_())
