import sys
import argparse
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout

class MainWindow(QMainWindow):
    def __init__(self, size=25):
        super().__init__()
        self.size = size

        self.setWindowTitle("Продвинутые методы визуализации 3D-полей")
        self.setGeometry(100, 100, 1200, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        plotters_layout = QHBoxLayout()
        main_layout.addLayout(plotters_layout)

        # Два окна для разных методов
        self.p1 = QtInteractor(self)
        self.p2 = QtInteractor(self)
        plotters_layout.addWidget(self.p1.interactor)
        plotters_layout.addWidget(self.p2.interactor)

        self.render_advanced_fields()
        self.show()

    def render_advanced_fields(self):
        # Генерируем 3D-сетку (по умолчанию разреженную, чтобы глифы не сливались)
        dims = (self.size,) * 3
        grid = pv.ImageData(dimensions=dims)
        grid.origin = (-2, -2, -2)
        grid.spacing = (4/(dims[0]-1), 4/(dims[1]-1), 4/(dims[2]-1))

        # Вычисляем скалярное поле (сложная интерференционная волна)
        points = grid.points
        X, Y, Z = points[:, 0], points[:, 1], points[:, 2]
        scalars = np.sin(X**2 + Y**2) * np.cos(Z)
        grid.point_data["Field"] = scalars

        # =====================================================================
        # ОКНО 1: Прямой объемный рендеринг (Volume Rendering)
        # =====================================================================
        self.p1.add_text("1. Volume Rendering (Объемный полупрозрачный газ)", position="upper_left", font_size=10)

        # Настройка непрозрачности (opacity): низкие значения прозрачные, высокие — плотные
        # Можно передать массив, строку вроде 'sigmoid', 'linear' или настроить руками
        opacity_transfer = [0.0, 0.0, 0.1, 0.3, 0.6, 0.8, 1.0]

        # Добавляем данные как объем (работает только для ImageData/UniformGrid)
        self.p1.add_volume(grid, scalars="Field", cmap="bone", opacity=opacity_transfer, shade=True)
        self.p1.show_grid()
        self.p1.reset_camera()

        # =====================================================================
        # ОКНО 2: Скалярные Глифы (Glyphs)
        # =====================================================================
        self.p2.add_text("2. Glyph (Масштабирование сфер по значению поля)", position="upper_left", font_size=10)

        # Берем модуль скаляра для адекватного масштаба диаметра сфер
        grid.point_data["AbsField"] = np.abs(scalars)

        # Создаем глифы: в каждую точку помещаем сферу, размер которой зависит от "AbsField"
        glyphs = grid.glyph(geom=pv.Sphere(), scale="AbsField", factor=0.4)

        # Отрисовываем получившийся массив сфер
        self.p2.add_mesh(glyphs, scalars="Field", cmap="coolwarm", show_edges=False)
        self.p2.show_grid()
        self.p2.reset_camera()

    def closeEvent(self, event):
        self.p1.close()
        self.p2.close()
        event.accept()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Продвинутая визуализация 3D-полей в PyVista")
    parser.add_argument("-n", "--size", type=int, default=25,
                        help="размер сетки по каждому измерению (по умолчанию 25)")
    args = parser.parse_args()
    if args.size < 2:
        parser.error("размер сетки должен быть >= 2")

    app = QApplication(sys.argv)
    window = MainWindow(args.size)
    sys.exit(app.exec())
