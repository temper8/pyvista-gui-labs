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

        self.setWindowTitle("Тороидальное поле на GPU (Оптимизация через Resampling)")
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

        # 2. Ползунок разрешения тора
        self.label_size = QLabel("Разрешение тора: 60x60", self)
        controls_layout.addWidget(self.label_size)
        self.slider_size = QSlider(Qt.Horizontal, self)
        self.slider_size.setMinimum(20)
        self.slider_size.setMaximum(150)  # Теперь можно смело повышать!
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
        self.plotter.add_text("GPU Accelerated Torus (Resampled)", position="upper_left", font_size=10)

        self.current_grid = None
        self.update_data_and_volume()
        self.plotter.reset_camera()
        self.show()

    def update_data_and_volume(self):
        """Генерирует тороидальное поле и интерполирует его в ImageData для GPU-рендеринга."""
        grid_dim = self.slider_size.value()
        n_angles = grid_dim
        n_radii = max(10, n_angles // 3)
        self.label_size.setText(f"Разрешение тора: {n_angles}x{n_angles}x{n_radii}")

        R_major = 3.0
        R_minor_max = 1.2

        # 1. Строим исходную математическую криволинейную сетку (StructuredGrid)
        phi = np.linspace(0, 2 * np.pi, n_angles)
        theta = np.linspace(0, 2 * np.pi, n_angles)
        r = np.linspace(0.1, R_minor_max, n_radii)

        PHI, THETA, R = np.meshgrid(phi, theta, r, indexing='ij')

        X = (R_major + R * np.cos(THETA)) * np.cos(PHI)
        Y = (R_major + R * np.cos(THETA)) * np.sin(PHI)
        Z = R * np.sin(THETA)

        torus_structured = pv.StructuredGrid(X, Y, Z)
        field = np.sin(3 * PHI + 2 * THETA) * (1.0 - (R / R_minor_max)**2)
        torus_structured.point_data["Field"] = field.ravel(order="F")

        # 2. ОПТИМИЗАЦИЯ: Создаем регулярный 3D-куб (ImageData), накрывающий тор в пространстве
        # Для идеального баланса четкости и FPS зафиксируем сетку куба на значении 80-100 точек
        box_dim = 90
        grid_gpu = pv.ImageData(dimensions=(box_dim, box_dim, box_dim))
        grid_gpu.origin = (-4.5, -4.5, -1.5)
        grid_gpu.spacing = (9.0 / (box_dim - 1), 9.0 / (box_dim - 1), 3.0 / (box_dim - 1))

        # 3. Переносим скалярное поле из изогнутого тора в куб через интерполяцию
        # Всё, что вне тора, автоматически станет нулевым (и прозрачным)
        resampled_box = grid_gpu.sample(torus_structured)

        # Сохраняем в кэш ресемплированный куб (ImageData)
        self.current_grid = resampled_box
        self.update_volume_only()

    def update_volume_only(self):
        """Мгновенно обновляет отображение на GPU при смене прозрачности/цвета."""
        if self.current_grid is None:
            return

        current_cmap = self.combo_cmap.currentText()
        opacity_factor = self.slider_opacity.value() / 100.0

        # Скрываем фоновые нулевые значения куба (все, что за пределами бублика),
        # а полезный сигнал внутри тора делаем видимым
        base_opacity = np.array([0.0, 0.0, 0.1, 0.4, 0.7, 0.9, 1.0])
        dynamic_opacity = base_opacity * opacity_factor

        # Теперь на вход подается ImageData, и GPU мгновенно подхватывает аппаратный рендеринг лучей
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
