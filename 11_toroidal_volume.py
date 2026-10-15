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

        self.setWindowTitle("Поле в тороидальной геометрии (Structured Volume)")
        self.setGeometry(100, 100, 1100, 800)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Панель управления ---
        controls_layout = QHBoxLayout()
        main_layout.addLayout(controls_layout)

        # 1. Выбор палитры
        controls_layout.addWidget(QLabel("Палитра:", self))
        self.combo_cmap = QComboBox(self)
        self.combo_cmap.addItems(["plasma", "viridis", "inferno", "coolwarm", "jet"])
        self.combo_cmap.currentIndexChanged.connect(self.update_volume_only)
        controls_layout.addWidget(self.combo_cmap)

        # 2. Ползунок разрешения сетки
        self.label_size = QLabel("Разрешение (углы/радиус): 60x60x20", self)
        controls_layout.addWidget(self.label_size)
        self.slider_size = QSlider(Qt.Horizontal, self)
        self.slider_size.setMinimum(20)
        self.slider_size.setMaximum(120)  # Сетка 120х120х30 дает ~430к точек (для StructuredGrid объемный рендеринг тяжелее)
        self.slider_size.setValue(60)
        self.slider_size.sliderReleased.connect(self.update_data_and_volume)
        controls_layout.addWidget(self.slider_size)

        # 3. Ползунок прозрачности
        controls_layout.addWidget(QLabel("Прозрачность:", self))
        self.slider_opacity = QSlider(Qt.Horizontal, self)
        self.slider_opacity.setMinimum(0)
        self.slider_opacity.setMaximum(100)
        self.slider_opacity.setValue(50)
        self.slider_opacity.valueChanged.connect(self.update_volume_only)
        controls_layout.addWidget(self.slider_opacity)

        # --- Окно PyVista ---
        self.plotter = QtInteractor(self)
        main_layout.addWidget(self.plotter.interactor)

        self.plotter.show_grid(color='gray')
        self.plotter.add_text("Toroidal Scalar Field", position="upper_left", font_size=10)

        self.current_grid = None
        self.update_data_and_volume()
        self.plotter.reset_camera()
        self.show()

    def update_data_and_volume(self):
        """Генерирует тороидальную сетку StructuredGrid и рассчитывает поле."""
        n_angles = self.slider_size.value()
        # Количество слоев по малому радиусу берем чуть меньше для пропорции
        n_radii = max(10, n_angles // 3)
        self.label_size.setText(f"Разрешение: {n_angles}x{n_angles}x{n_radii}")

        # 1. Задаем параметры геометрии тора
        R_major = 3.0  # Расстояние от центра бублика до центра трубы
        R_minor_max = 1.2  # Максимальный радиус самой трубы

        # 2. Создаем сетку в тороидальных координатах (phi, theta, r)
        phi = np.linspace(0, 2 * np.pi, n_angles)      # Угол вокруг главной оси Z
        theta = np.linspace(0, 2 * np.pi, n_angles)    # Угол обхода вокруг трубы тора
        r = np.linspace(0.1, R_minor_max, n_radii)     # Радиус от центра трубы (отсекаем ноль для красоты ядра)

        # Создаем 3D meshgrid
        PHI, THETA, R = np.meshgrid(phi, theta, r, indexing='ij')

        # 3. Переводим тороидальные координаты в декартовы (X, Y, Z) для построения геометрии
        X = (R_major + R * np.cos(THETA)) * np.cos(PHI)
        Y = (R_major + R * np.cos(THETA)) * np.sin(PHI)
        Z = R * np.sin(THETA)

        # 4. Создаем StructuredGrid (структурированную криволинейную сетку)
        grid = pv.StructuredGrid(X, Y, Z)

        # 5. Генерируем винтовое скалярное поле внутри тора
        # Поле закручивается по спирали (зависит от комбинации углов PHI и THETA) и затухает к краям трубы
        field = np.sin(3 * PHI + 2 * THETA) * (1.0 - (R / R_minor_max)**2)

        # Привязываем скаляры к точкам сетки (порядок "F" критичен для VTK)
        grid.point_data["Field"] = field.ravel(order="F")

        self.current_grid = grid
        self.update_volume_only()

    def update_volume_only(self):
        """Мгновенно обновляет визуализацию тора (прозрачность, цвет)."""
        if self.current_grid is None:
            return

        current_cmap = self.combo_cmap.currentText()
        opacity_factor = self.slider_opacity.value() / 100.0

        # Передаточная функция прозрачности
        base_opacity = np.array([0.0, 0.1, 0.4, 0.7, 0.9, 1.0])
        dynamic_opacity = base_opacity * opacity_factor

        # Для StructuredGrid метод add_volume тоже отлично работает!
        # Он берет криволинейные ячейки и честно проецирует лучи сквозь изогнутый объем
        self.plotter.add_volume(
            self.current_grid,
            scalars="Field",
            cmap=current_cmap,
            opacity=list(dynamic_opacity),
            shade=True,
            name="toroidal_volume",
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
