import sys
from PyQt5.QtWidgets import QApplication
from frontend.MainWindow2 import MainWindow
from backend.backend import Backend


# Authors: Michaël Marsset, Claudia Rodríguez. 2024

if __name__ == '__main__':

    print(f"{'-' * 10} ** PREVENTING STELLAR CONTAMINATION IN MOVING OBJECTS ** {'-' * 10}")

    # For printing errors in the terminal.
    def hook(type_, value, traceback):
        print(type_)
        print(traceback)

    sys.__excepthook__ = hook
    app =  QApplication([])

    # Creating an instance of the front and back end windows
    back = Backend()
    front = MainWindow()

    # Signal connecting
    front.signal_valid_input.connect(back.validation)
    back.signal_error.connect(front.error)
    back.signal_plot.connect(front.plot)
    back.signal_splot.connect(front.single_plot)
    back.signal_progress.connect(front.update_progbar)
    back.signal_flags.connect(front.update_flags)
    # back.signal_dates.connect(front.update_datebox)
    front.signal_date.connect(back.send_skyfov)
    back.signal_skyfov.connect(front.plot_fov)


    # Showing the window.
    front.show()
    sys.exit(app.exec())
