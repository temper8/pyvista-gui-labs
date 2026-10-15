import sys
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QSlider, QComboBox, QLabel)
from PySide6.QtCore import Qt
from scipy.special import assoc_laguerre, sph_harm_y

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Квантовые орбитали водорода в 3D (Volume Rendering)")
        self.setGeometry(100, 100, 1100, 850)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Панель управления ---
        controls_layout = QHBoxLayout()
        main_layout.addLayout(controls_layout)

        # 1. Выбор орбитали (Квантовые числа n, l, m)
        controls_layout.addWidget(QLabel("Орбиталь (n, l, m):", self))
        self.combo_orbital = QComboBox(self)
        self.combo_orbital.addItems([
            "1s (1, 0, 0) - Сфера",
            "2p (2, 1, 0) - Гантель",
            "3d (3, 2, 0) - Четырехлистник",
            "4f (4, 3, 0) - Сложная форма"
        ])
        self.combo_orbital.currentIndexChanged.connect(self.update_data_and_volume)
        controls_layout.addWidget(self.combo_orbital)

        # 2. Выбор палитры
        controls_layout.addWidget(QLabel("Палитра:", self))
        self.combo_cmap = QComboBox(self)
        self.combo_cmap.addItems(["inferno", "magma", "plasma", "viridis", "coolwarm"])
        self.combo_cmap.currentIndexChanged.connect(self.update_volume_only)
        controls_layout.addWidget(self.combo_cmap)

        # 3. Ползунок разрешения
        self.label_size = QLabel("Сетка: 80x80x80", self)
        controls_layout.addWidget(self.label_size)
        self.slider_size = QSlider(Qt.Horizontal, self)
        self.slider_size.setMinimum(30)
        self.slider_size.setMaximum(200)  # Оптимально для квантовых функций
        self.slider_size.setValue(80)
        self.slider_size.sliderReleased.connect(self.update_data_and_volume)
        controls_layout.addWidget(self.slider_size)

        # 4. Ползунок прозрачности
        controls_layout.addWidget(QLabel("Прозрачность:", self))
        self.slider_opacity = QSlider(Qt.Horizontal, self)
        self.slider_opacity.setMinimum(0)
        self.slider_opacity.setMaximum(100)
        self.slider_opacity.setValue(60)
        self.slider_opacity.valueChanged.connect(self.update_volume_only)
        controls_layout.addWidget(self.slider_opacity)

        # --- Окно PyVista ---
        self.plotter = QtInteractor(self)
        main_layout.addWidget(self.plotter.interactor)

        self.plotter.show_grid(color='gray', xtitle='X (Bohr)', ytitle='Y (Bohr)', ztitle='Z (Bohr)')
        self.plotter.add_text("Hydrogen Electron Orbitals", position="upper_left", font_size=10)

        self.current_grid = None
        self.update_data_and_volume()
        self.plotter.reset_camera()
        self.show()

    def calculate_psi(self, x, y, z, n, l, m):
        """Вычисляет плотность вероятности |Psi|^2 для атома водорода."""
        # Переводим декартовы координаты в сферические (r, theta, phi)
        r = np.sqrt(x**2 + y**2 + z**2)
        # Избегаем деления на ноль в центре
        r = np.where(r == 0, 1e-9, r)

        theta = np.arccos(z / r)
        phi = np.arctan2(y, x)

        # 1. Радиальная часть волновой функции R(r)
        rho = 2.0 * r / n
        # Нормировочный коэффициент (упрощенный для визуализации масштаба)
        laguerre = assoc_laguerre(rho, n - l - 1, 2 * l + 1)
        R = (rho**l) * laguerre * np.exp(-rho / 2.0)

        # 2. Угловая часть (Сферические гармоники Y_lm)
        # sph_harm_y принимает (l, m, theta, phi), где theta — полярный угол, phi — азимут
        Y = sph_harm_y(l, m, theta, phi)

        # Полная волновая функция Psi и плотность вероятности |Psi|^2
        psi = R * Y
        prob_density = np.abs(psi)**2
        return prob_density

    def update_data_and_volume(self):
        """Перерасчет квантового поля волновой функции электрона."""
        grid_dim = self.slider_size.value()
        orbital_text = self.combo_orbital.currentText()
        self.label_size.setText(f"Сетка: {grid_dim}x{grid_dim}x{grid_dim}")

        # Парсим квантовые числа из текста комбобокса
        if "1s" in orbital_text: n, l, m = 1, 0, 0
        elif "2p" in orbital_text: n, l, m = 2, 1, 0
        elif "3d" in orbital_text: n, l, m = 3, 2, 0
        elif "4f" in orbital_text: n, l, m = 4, 3, 0

        # Масштабируем область обзора в зависимости от главного квантового числа n (орбиталь растет с n)
        box_size = n * 7.0

        # Создаем 3D сетку объема
        grid = pv.ImageData(dimensions=(grid_dim, grid_dim, grid_dim))
        grid.origin = (-box_size, -box_size, -box_size)
        grid.spacing = (2 * box_size / (grid_dim - 1), 2 * box_size / (grid_dim - 1), 2 * box_size / (grid_dim - 1))

        # Вычисляем поле
        X, Y, Z = grid.points[:, 0], grid.points[:, 1], grid.points[:, 2]
        density = self.calculate_psi(X, Y, Z, n, l, m)

        # Нормализуем значения от 0 до 1 для удобства рендеринга
        if np.max(density) > 0:
            density = density / np.max(density)

        grid.point_data["Probability"] = density.ravel(order="F")
        self.current_grid = grid

        self.update_volume_only()

    def update_volume_only(self):
        """Быстрое обновление шейдеров палитры и прозрачности."""
        if self.current_grid is None:
            return

        current_cmap = self.combo_cmap.currentText()
        opacity_factor = self.slider_opacity.value() / 100.0

        # График прозрачности: убираем совсем слабый фоновый шум (около 0),
        # а зоны высокой вероятности делаем яркими и светящимися
        base_opacity = np.array([0.0, 0.0, 0.05, 0.2, 0.5, 0.8, 1.0])
        dynamic_opacity = base_opacity * opacity_factor

        self.plotter.add_volume(
            self.current_grid,
            scalars="Probability",
            cmap=current_cmap,
            opacity=list(dynamic_opacity),
            shade=True,
            name="quantum_volume",
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
