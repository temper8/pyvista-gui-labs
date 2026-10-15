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

        self.setWindowTitle("3D-генератор с управлением прозрачностью")
        self.setGeometry(100, 100, 1100, 800)

        # Главный интерфейс
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Панель управления ---
        controls_layout = QHBoxLayout()
        main_layout.addLayout(controls_layout)

        # 1. Выбор функции
        controls_layout.addWidget(QLabel("Функция:", self))
        self.combo_func = QComboBox(self)
        self.combo_func.addItems(["Интерференционная волна", "3D-Гироид (Structure)", "Тороидальный узел"])
        self.combo_func.currentIndexChanged.connect(self.update_data_and_volume)
        controls_layout.addWidget(self.combo_func)

        # 2. Выбор палитры
        controls_layout.addWidget(QLabel("Палитра:", self))
        self.combo_cmap = QComboBox(self)
        self.combo_cmap.addItems(["magma", "plasma", "viridis", "inferno", "coolwarm", "jet", "bone"])
        self.combo_cmap.currentIndexChanged.connect(self.update_volume_only)
        controls_layout.addWidget(self.combo_cmap)

        # 3. Ползунок разрешения (Сетка)
        self.label_size = QLabel("Сетка: 60x60x60", self)
        controls_layout.addWidget(self.label_size)
        self.slider_size = QSlider(Qt.Horizontal, self)
        self.slider_size.setMinimum(20)
        self.slider_size.setMaximum(250)
        self.slider_size.setValue(60)
        self.slider_size.sliderReleased.connect(self.update_data_and_volume)
        controls_layout.addWidget(self.slider_size)

        # 4. Ползунок прозрачности (Opacity)
        controls_layout.addWidget(QLabel("Прозрачность:", self))
        self.slider_opacity = QSlider(Qt.Horizontal, self)
        self.slider_opacity.setMinimum(0)
        self.slider_opacity.setMaximum(100)
        self.slider_opacity.setValue(50)  # По умолчанию 50%
        # Используем valueChanged, так как смена прозрачности в VTK происходит мгновенно и не лагает
        self.slider_opacity.valueChanged.connect(self.update_volume_only)
        controls_layout.addWidget(self.slider_opacity)

        # --- Окно визуализации ---
        self.plotter = QtInteractor(self)
        main_layout.addWidget(self.plotter.interactor)

        self.plotter.show_grid(color='gray')
        self.plotter.add_text("Volume Rendering + Opacity Control", position="upper_left", font_size=10)

        # Глобальные переменные для кэширования сетки, чтобы не пересчитывать её при изменении только прозрачности/цвета
        self.current_grid = None

        # Первый запуск (генерируем и данные, и объём)
        self.update_data_and_volume()
        self.plotter.reset_camera()
        self.show()

    def update_data_and_volume(self):
        """Полный перерасчет математической сетки (вызывается при смене функции или размера сетки)."""
        grid_dim = self.slider_size.value()
        func_type = self.combo_func.currentText()
        self.label_size.setText(f"Сетка: {grid_dim}x{grid_dim}x{grid_dim}")

        # Создаем ImageData
        dims = (grid_dim, grid_dim, grid_dim)
        grid = pv.ImageData(dimensions=dims)
        grid.origin = (-3, -3, -3)
        grid.spacing = (6 / (grid_dim - 1), 6 / (grid_dim - 1), 6 / (grid_dim - 1))

        # Вытаскиваем координаты и считаем NumPy поле
        points = grid.points
        X, Y, Z = points[:, 0], points[:, 1], points[:, 2]

        if func_type == "Интерференционная волна":
            R = np.sqrt(X**2 + Y**2 + Z**2)
            scalars = np.sin(R**2) / (R + 0.5)
        elif func_type == "3D-Гироид (Structure)":
            scalars = np.sin(2*X) * np.cos(2*Y) + np.sin(2*Y) * np.cos(2*Z) + np.sin(2*Z) * np.cos(2*X)
        else:  # Тороидальный узел
            r_torus = 1.5
            r_current = np.sqrt(X**2 + Y**2)
            phi = np.arctan2(Y, X)
            dist_to_axis = np.sqrt((r_current - r_torus)**2 + Z**2)
            scalars = np.sin(5 * phi + 3 * np.arctan2(Z, r_current - r_torus)) * np.exp(-dist_to_axis**2)

        grid.point_data["Field"] = scalars.ravel(order="F")

        # Сохраняем в кэш класса
        self.current_grid = grid

        # Переходим к отрисовке
        self.update_volume_only()

    def update_volume_only(self):
        """Быстрое обновление только визуальных свойств (палитра, прозрачность) без пересчета NumPy-матрицы."""
        if self.current_grid is None:
            return

        current_cmap = self.combo_cmap.currentText()
        func_type = self.combo_func.currentText()

        # Получаем коэффициент прозрачности от 0.0 до 1.0 из слайдера Qt
        opacity_factor = self.slider_opacity.value() / 100.0

        # Формируем базовые профили прозрачности в зависимости от структуры
        if func_type == "3D-Гироид (Structure)":
            # Для гироида: края плотные, центр пустой (чтобы видеть поры)
            base_opacity = np.array([1.0, 0.4, 0.0, 0.0, 0.0, 0.4, 1.0])
        else:
            # Для волн и узла: плавное нарастание плотности к пиковым значениям
            base_opacity = np.array([0.0, 0.0, 0.1, 0.4, 0.7, 0.9, 1.0])

        # Применяем множитель прозрачности от слайдера
        dynamic_opacity = base_opacity * opacity_factor

        # Обновляем объём в плоттере. Благодаря одинаковому 'name' VTK просто меняет свойства отображения
        self.plotter.add_volume(
            self.current_grid,
            scalars="Field",
            cmap=current_cmap,
            opacity=list(dynamic_opacity),
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
