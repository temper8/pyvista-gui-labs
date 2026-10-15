import sys
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QSlider, QComboBox, QLabel)
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Генератор 3D-полей высокого разрешения")
        self.setGeometry(100, 100, 1100, 750)

        # Главный интерфейс
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Панель управления ---
        controls_layout = QHBoxLayout()
        main_layout.addLayout(controls_layout)

        # 1. Выбор функции
        controls_layout.addWidget(QLabel("Функция поля:", self))
        self.combo_func = QComboBox(self)
        self.combo_func.addItems(["Интерференционная волна", "3D-Гироид (Stucture)", "Тороидальный узел"])
        self.combo_func.currentIndexChanged.connect(self.update_volume)
        controls_layout.addWidget(self.combo_func)

        controls_layout.addSpacing(15)

        # 2. Выбор палитры
        controls_layout.addWidget(QLabel("Палитра:", self))
        self.combo_cmap = QComboBox(self)
        self.combo_cmap.addItems(["magma", "plasma", "viridis", "inferno", "coolwarm", "jet", "bone"])
        self.combo_cmap.currentIndexChanged.connect(self.update_volume)
        controls_layout.addWidget(self.combo_cmap)

        controls_layout.addSpacing(15)

        # 3. Ползунок разрешения
        self.label_size = QLabel("Сетка: 60x60x60", self)
        controls_layout.addWidget(self.label_size)

        self.slider_size = QSlider(Qt.Horizontal, self)
        self.slider_size.setMinimum(20)
        self.slider_size.setMaximum(250)  # ЛИМИТ ПОВЫШЕН ДО 250! (~15.6 млн вокселей)
        self.slider_size.setValue(60)
        self.slider_size.setTickInterval(20)
        self.slider_size.setTickPosition(QSlider.TicksBelow)
        self.slider_size.sliderReleased.connect(self.update_volume)
        controls_layout.addWidget(self.slider_size)

        # --- Окно визуализации ---
        self.plotter = QtInteractor(self)
        main_layout.addWidget(self.plotter.interactor)

        # Настраиваем сцену один раз
        self.plotter.show_grid(color='gray')
        self.plotter.add_text("Ultra High-Res Volume", position="upper_left", font_size=10)

        # Первый запуск
        self.update_volume()
        self.plotter.reset_camera()
        self.show()

    def update_volume(self):
        """Перерасчитывает выбранное поле и принудительно обновляет 3D-объем."""
        grid_dim = self.slider_size.value()
        current_cmap = self.combo_cmap.currentText()
        func_type = self.combo_func.currentText()

        self.label_size.setText(f"Сетка: {grid_dim}x{grid_dim}x{grid_dim}")

        # 1. Быстрое создание сетки нужного размера
        dims = (grid_dim, grid_dim, grid_dim)
        grid = pv.ImageData(dimensions=dims)
        grid.origin = (-3, -3, -3)
        grid.spacing = (6 / (grid_dim - 1), 6 / (grid_dim - 1), 6 / (grid_dim - 1))

        # 2. Вытаскиваем координаты точек одним массивом для оптимизации расчетов
        points = grid.points
        X, Y, Z = points[:, 0], points[:, 1], points[:, 2]

        # 3. Расчет выбранного математического поля (векторизованный через NumPy)
        if func_type == "Интерференционная волна":
            # Сферические волны с затуханием от центра
            R = np.sqrt(X**2 + Y**2 + Z**2)
            scalars = np.sin(R**2) / (R + 0.5)
            opacity_transfer = [0.0, 0.0, 0.1, 0.3, 0.5, 0.8, 1.0]

        elif func_type == "3D-Гироид (Stucture)":
            # Формула гироида: sin(x)cos(y) + sin(y)cos(z) + sin(z)cos(x)
            # Масштабируем координаты, чтобы получить красивую периодичность
            scalars = np.sin(2*X) * np.cos(2*Y) + np.sin(2*Y) * np.cos(2*Z) + np.sin(2*Z) * np.cos(2*X)
            # Для гироида делаем прозрачной сердцевину, оставляя видимыми только стенки структуры
            opacity_transfer = [1.0, 0.4, 0.0, 0.0, 0.0, 0.4, 1.0]

        else:  # Тороидальный узел
            # Переплетение полей вокруг тора
            r_torus = 1.5
            r_current = np.sqrt(X**2 + Y**2)
            phi = np.arctan2(Y, X)
            # Расстояние от оси тора
            dist_to_axis = np.sqrt((r_current - r_torus)**2 + Z**2)
            scalars = np.sin(5 * phi + 3 * np.arctan2(Z, r_current - r_torus)) * np.exp(-dist_to_axis**2)
            opacity_transfer = [0.0, 0.0, 0.1, 0.4, 0.7, 0.9, 1.0]

        # Привязываем массив данных (order="F" обязателен для VTK структур)
        grid.point_data["Field"] = scalars.ravel(order="F")

        # 4. Рендеринг в память VTK с фиксацией имени 'name' для мгновенной перерисовки
        self.plotter.add_volume(
            grid,
            scalars="Field",
            cmap=current_cmap,
            opacity=opacity_transfer,
            shade=True,
            name="high_res_volume",
            show_scalar_bar=False
        )

        self.plotter.render()

    def closeEvent(self, event):
        self.plotter.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
