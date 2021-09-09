import sys
# sys.path.append('c:/Users/XiaYoung/codes/XYNodeEditor')

from PySide2.QtWidgets import QApplication, QStyleFactory

from examples.example_calculator.calc_window import CalculatorWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # print(QStyleFactory.keys())

    app.setStyle('Fusion')

    wnd = CalculatorWindow()
    wnd.show()

    sys.exit(app.exec_())
