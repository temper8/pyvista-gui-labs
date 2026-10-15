import sys
import random
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
import pyvista as pv
from pyvistaqt import QtInteractor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Настройка главного окна
        self.setWindowTitle("Интеграция PyVista и PySide6")
        self.setGeometry(100, 100, 800, 600)

        # Создаем центральный виджет и вертикальный слой
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Создаем интерактивный виджет PyVista для Qt
        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)

        # Добавляем кнопку для взаимодействия
        self.button = QPushButton("Добавить случайную фигуру", self)
        self.button.clicked.connect(self.add_random_mesh)
        layout.addWidget(self.button)

        # Отображаем начальную фигуру
        self.current_mesh = None
        self.add_random_mesh()

        # Показываем окно
        self.show()

    def add_random_mesh(self):
        """Очищает сцену и добавляет случайную 3D-фигуру."""
        # Очищаем старые меши из сцены
        self.plotter.clear()

        # Выбираем случайную фигуру
        mesh_type = random.choice(["sphere", "cube", "cylinder"])

        if mesh_type == "sphere":
            mesh = pv.Sphere()
            color = "crimson"
        elif mesh_type == "cube":
            mesh = pv.Cube()
            color = "teal"
        else:
            mesh = pv.Cylinder()
            color = "gold"

        # Добавляем фигуру на сцену PyVista
        self.plotter.add_mesh(mesh, color=color, show_edges=True)

        # Сбрасываем камеру, чтобы фигура была по центру
        self.plotter.reset_camera()

    def closeEvent(self, event):
        """Обязательно закрываем плоттер при закрытии окна, чтобы избежать зависания VTK."""
        self.plotter.close()
        event.accept()

if __name__ == "__main__":
    # Инициализация приложения Qt
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
