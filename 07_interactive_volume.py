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

        self.setWindowTitle("Интерактивный Volume Rendering в PySide6")
        self.setGeometry(100, 100, 1000, 700)

        # Главный контейнер
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Блок управления (Верхняя панель) ---
        controls_layout = QHBoxLayout()
        main_layout.addLayout(controls_layout)

        # Выбор палитры (Colormap)
        controls_layout.addWidget(QLabel("Палитра:", self))
        self.combo_cmap = QComboBox(self)
        self.combo_cmap.addItems(["bone", "viridis", "plasma", "inferno", "coolwarm", "magma", "jet"])
        # Меняем сигнал на currentIndexChanged, он стабильнее работает при обновлении
        self.combo_cmap.currentIndexChanged.connect(self.update_volume)
        controls_layout.addWidget(self.combo_cmap)

        controls_layout.addSpacing(20)

        # Ползунок размера сетки
        self.label_size = QLabel("Размер сетки: 40x40x40", self)
        controls_layout.addWidget(self.label_size)

        self.slider_size = QSlider(Qt.Horizontal, self)
        self.slider_size.setMinimum(10)
        self.slider_size.setMaximum(120)  # Лимиты повышены до 120!
        self.slider_size.setValue(40)
        self.slider_size.setTickInterval(10)
        self.slider_size.setTickPosition(QSlider.TicksBelow)
        self.slider_size.sliderReleased.connect(self.update_volume)
        controls_layout.addWidget(self.slider_size)

        # --- Блок визуализации (PyVista) ---
        self.plotter = QtInteractor(self)
        main_layout.addWidget(self.plotter.interactor)

        # Добавляем статичную сетку один раз, чтобы она не мерцала при обновлении
        self.plotter.show_grid(color='gray')
        self.plotter.add_text("Volume Rendering", position="upper_left", font_size=10)

        # Первичный запуск отрисовки
        self.update_volume()

        # Сбрасываем камеру только при самом первом старте
        self.plotter.reset_camera()
        self.show()

    def update_volume(self):
        """Перегенерирует 3D-данные и принудительно обновляет объемный рендеринг."""
        grid_dim = self.slider_size.value()
        current_cmap = self.combo_cmap.currentText()

        # Обновляем текст лейбла
        self.label_size.setText(f"Размер сетки: {grid_dim}x{grid_dim}x{grid_dim}")

        # 1. Генерируем ImageData с динамическим разрешением
        dims = (grid_dim, grid_dim, grid_dim)
        grid = pv.ImageData(dimensions=dims)
        grid.origin = (-2, -2, -2)
        grid.spacing = (4 / (grid_dim - 1), 4 / (grid_dim - 1), 4 / (grid_dim - 1))

        # 2. Вычисляем скалярное поле
        points = grid.points
        X, Y, Z = points[:, 0], points[:, 1], points[:, 2]
        scalars = np.sin(X**2 + Y**2) * np.cos(Z)
        grid.point_data["Field"] = scalars

        # 3. Настройка прозрачности (Transfer Function)
        opacity_transfer = [0.0, 0.05, 0.1, 0.3, 0.6, 0.8, 1.0]

        # 4. Добавляем объемный рендеринг с жестким указанием имени 'name'.
        # Это заставляет PyVista переписывать актера в памяти VTK и обновлять текстуры/палитры.
        self.plotter.add_volume(
            grid,
            scalars="Field",
            cmap=current_cmap,
            opacity=opacity_transfer,
            shade=True,
            name="my_interactive_volume",  # Ключевое исправление бага палитры!
            show_scalar_bar=False         # Скрываем шкалу, чтобы она не перерисовывалась бесконечно
        )

        # Обновляем картинку без сброса положения камеры
        self.plotter.render()

    def closeEvent(self, event):
        self.plotter.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
