import sys
from PyQt5.QtWidgets import QApplication
from frontend.NewMainWindow import MainWindow
from backend.NewBackend import Backend


# Authors: Michaël Marsset, Claudia Rodríguez. 2024

if __name__ == '__main__':

    print(f"{'-' * 10} ** PREVENTING STELLAR CONTAMINATION IN MOVING OBJECTS ** {'-' * 10}")

    # For printing errors in the terminal.
    def hook(type_, value, traceback):
        print(type_)
        print(traceback)

    sys.__excepthook__ = hook
    app =  QApplication([])
    app.setStyle('Fusions')

    # Creating an instance of the front and back end windows
    back = Backend()
    front = MainWindow()

    # Signal connecting
    front.signal_start.connect(back.start_worker)
    front.signal_pa.connect(back.calculate_pa)
    back.signal_pangle.connect(front.update_rot)
    back.signal_error.connect(front.error)
    back.signal_plot.connect(front.plot)
    back.signal_splot.connect(front.single_plot)
    back.signal_progress.connect(front.update_progbar)
    back.signal_flags.connect(front.update_table)
    back.signal_best.connect(front.update_bestseen)
    #front.signal_date.connect(back.send_skyfov)



    # Showing the window.
    front.show()
    sys.exit(app.exec())
