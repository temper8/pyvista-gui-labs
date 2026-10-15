import sys
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("3D-аналог pcolormesh (Воксели и Объемные данные)")
        self.setGeometry(100, 100, 1200, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Создаем два окна рядом для сравнения подходов
        plotters_layout = QHBoxLayout()
        main_layout.addLayout(plotters_layout)

        self.p1 = QtInteractor(self)
        self.p2 = QtInteractor(self)
        plotters_layout.addWidget(self.p1.interactor)
        plotters_layout.addWidget(self.p2.interactor)

        # Генерация данных и их отрисовка
        self.visualize_3d_data()
        self.show()

    def visualize_3d_data(self):
        # 1. Генерируем 3D-сетку координат (например, размер 40x40x40 ячеек)
        dims = (40, 40, 40)
        x = np.linspace(-2, 2, dims[0])
        y = np.linspace(-2, 2, dims[1])
        z = np.linspace(-2, 2, dims[2])
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

        # 2. Вычисляем скалярное 3D-поле (функция плотности: сферы с затуханием)
        # Это честный 3D-аналог матрицы для pcolormesh
        values = np.sin(np.sqrt(X**2 + Y**2 + Z**2) * np.pi)

        # 3. Создаем структуру данных PyVista для регулярной 3D-сетки
        # Задаем размеры и шаг (spacing) между точками
        grid = pv.ImageData(dimensions=dims)
        grid.origin = (-2, -2, -2)
        grid.spacing = (4 / (dims[0]-1), 4 / (dims[1]-1), 4 / (dims[2]-1))

        # Привязываем наши трехмерные данные к точкам сетки
        # Разворачиваем 3D-массив в 1D (в формате VTK порядок "F")
        grid.point_data["Density"] = values.ravel(order="F")

        # =====================================================================
        # ОКНО 1: Честные воксели (Объемная закраска через Порог / Threshold)
        # =====================================================================
        self.p1.add_text("1. Воксели (Ценз по плотности > 0.2)", position="upper_left", font_size=10)

        # С помощью threshold отсекаем пустые области, оставляя только "плотное" вещество,
        # превращая ячейки сетки в видимые кубики (воксели).
        voxels = grid.threshold(0.2, scalars="Density")

        self.p1.add_mesh(voxels, scalars="Density", cmap="plasma", show_edges=True, edge_color="black")
        self.p1.show_grid()
        self.p1.reset_camera()

        # =====================================================================
        # ОКНО 2: Срезы (Slices) и Изоповерхности (Isosurfaces)
        # =====================================================================
        self.p2.add_text("2. Ортогональные срезы + Изоповерхность", position="upper_left", font_size=10)

        # Вариант А: Интерактивные срезы по осям X, Y, Z
        slices = grid.slice_orthogonal(x=0, y=0, z=0)
        self.p2.add_mesh(slices, scalars="Density", cmap="plasma", opacity=0.8)

        # Вариант Б: Контурная изоповерхность (уровень равной плотности, аналог contour в 2D)
        contours = grid.contour(isosurfaces=[0.6], scalars="Density")
        self.p2.add_mesh(contours, color="cyan", opacity=0.4, style="wireframe")

        self.p2.show_grid()
        self.p2.reset_camera()

    def closeEvent(self, event):
        self.p1.close()
        self.p2.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
