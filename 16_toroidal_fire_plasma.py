import sys
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QSpinBox, QDoubleSpinBox, QComboBox,
                             QLabel, QPushButton, QGroupBox, QCheckBox)
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Тороидальное пламя на белом фоне (Fire Plasma Torus)")
        self.setGeometry(100, 100, 1200, 850)

        # Главный контейнер
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # =====================================================================
        # ЛЕВАЯ ПАНЕЛЬ: Элементы управления
        # =====================================================================
        controls_widget = QWidget(self)
        controls_widget.setFixedWidth(320)
        controls_layout = QVBoxLayout(controls_widget)
        main_layout.addWidget(controls_widget)

        # Группа 1: Разрешение сеток
        group_res = QGroupBox("Разрешение (Resolution)", self)
        res_layout = QVBoxLayout(group_res)

        res_layout.addWidget(QLabel("Текстура GPU (box_dim):", self))
        self.spin_box_dim = QSpinBox(self)
        self.spin_box_dim.setRange(20, 300)
        self.spin_box_dim.setValue(100)
        res_layout.addWidget(self.spin_box_dim)

        controls_layout.addWidget(group_res)

        # Группа 2: Частоты поля
        group_freq = QGroupBox("Параметры поля (Frequencies)", self)
        freq_layout = QVBoxLayout(group_freq)

        freq_layout.addWidget(QLabel("Главная частота (вокруг Z):", self))
        self.spin_freq_phi = QSpinBox(self)
        self.spin_freq_phi.setRange(0, 20)
        self.spin_freq_phi.setValue(3)
        freq_layout.addWidget(self.spin_freq_phi)

        freq_layout.addWidget(QLabel("Малая частота (вокруг трубы):", self))
        self.spin_freq_theta = QSpinBox(self)
        self.spin_freq_theta.setRange(0, 20)
        self.spin_freq_theta.setValue(2)
        freq_layout.addWidget(self.spin_freq_theta)

        controls_layout.addWidget(group_freq)

        # Группа 3: Угловой вырез
        group_clip = QGroupBox("Сечение объема (Angular Cut)", self)
        clip_layout = QVBoxLayout(group_clip)

        self.check_clip = QCheckBox("Включить угловой вырез", self)
        self.check_clip.setChecked(True)
        clip_layout.addWidget(self.check_clip)

        clip_layout.addWidget(QLabel("Угол выреза (в градусах):", self))
        self.spin_cut_angle = QSpinBox(self)
        self.spin_cut_angle.setRange(0, 360)
        self.spin_cut_angle.setSingleStep(15)
        self.spin_cut_angle.setValue(90)
        clip_layout.addWidget(self.spin_cut_angle)

        controls_layout.addWidget(group_clip)

        # Группа 4: Оптика и свет
        group_vis = QGroupBox("Оптика пламени", self)
        vis_layout = QVBoxLayout(group_vis)

        vis_layout.addWidget(QLabel("Прозрачность (0.0 - 1.0):", self))
        self.spin_opacity = QDoubleSpinBox(self)
        self.spin_opacity.setRange(0.0, 1.0)
        self.spin_opacity.setSingleStep(0.05)
        self.spin_opacity.setValue(0.60)
        vis_layout.addWidget(self.spin_opacity)

        vis_layout.addWidget(QLabel("Внутреннее свечение (Ambient):", self))
        self.spin_ambient = QDoubleSpinBox(self)
        self.spin_ambient.setRange(0.0, 1.0)
        self.spin_ambient.setSingleStep(0.1)
        self.spin_ambient.setValue(0.3)
        vis_layout.addWidget(self.spin_ambient)

        controls_layout.addWidget(group_vis)

        # Кнопка обновления
        controls_layout.addSpacing(10)
        self.btn_update = QPushButton("🔥 Зажечь плазму", self)
        self.btn_update.setStyleSheet("font-weight: bold; font-size: 14px; padding: 8px;")
        self.btn_update.clicked.connect(self.generate_and_render)
        controls_layout.addWidget(self.btn_update)

        controls_layout.addStretch()

        # =====================================================================
        # ПРАВАЯ ПАНЕЛЬ: Окно 3D Визуализации PyVista
        # =====================================================================
        self.plotter = QtInteractor(self)
        main_layout.addWidget(self.plotter.interactor)

        # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Задаем абсолютно белый студийный фон
        self.plotter.set_background("white")
        self.plotter.show_grid(color='lightgray')
        self.plotter.add_text("Toroidal Fire Plasma Simulation", position="upper_left", font_size=10, color="black")

        # Первичный запуск отрисовки
        self.generate_and_render()
        self.plotter.reset_camera()
        self.show()

    def generate_and_render(self):
        """Полный перерасчет тороидального объема в огненной палитре."""
        box_dim = self.spin_box_dim.value()
        opacity_factor = self.spin_opacity.value()
        ambient_value = self.spin_ambient.value()

        freq_phi = self.spin_freq_phi.value()
        freq_theta = self.spin_freq_theta.value()

        is_clip_enabled = self.check_clip.isChecked()
        cut_angle_deg = self.spin_cut_angle.value()
        cut_angle_rad = np.radians(cut_angle_deg)

        R_major = 3.0
        R_minor_max = 1.2

        # 1. Создаем ImageData (Текстура GPU)
        grid_gpu = pv.ImageData(dimensions=(box_dim, box_dim, box_dim))
        grid_gpu.origin = (-4.5, -4.5, -1.5)
        grid_gpu.spacing = (9.0 / (box_dim - 1), 9.0 / (box_dim - 1), 3.0 / (box_dim - 1))

        # 2. Декартовы координаты
        points = grid_gpu.points
        X, Y, Z = points[:, 0], points[:, 1], points[:, 2]

        # 3. Обратное вычисление тороидальной геометрии
        PHI = np.arctan2(Y, X)
        PHI_pos = np.where(PHI >= 0, PHI, PHI + 2 * np.pi)

        r_current = np.sqrt(X**2 + Y**2)
        THETA = np.arctan2(Z, r_current - R_major)
        R = np.sqrt((r_current - R_major)**2 + Z**2)

        # 4. Расчет математического поля
        field = np.sin(freq_phi * PHI + freq_theta * THETA) * (1.0 - (R / R_minor_max)**2)

        # Маскирование А: зануление за пределами физических границ тора
        field = np.where(R <= R_minor_max, field, 0.0)

        # Маскирование Б: Угловой клиппинг сектора «пирога» [2.1]
        if is_clip_enabled and cut_angle_rad > 0:
            field = np.where((PHI_pos >= 0) & (PHI_pos <= cut_angle_rad), 0.0, field)

        # Модуль для идеальной прозрачности фона и вырезанного сегмента
        field_abs = np.abs(field)

        # Ограничиваем интенсивность в строгие рамки 0.0 - 1.0 для корректной работы кастомной палитры
        field_abs = np.clip(field_abs, 0.0, 1.0)
        grid_gpu.point_data["Field"] = field_abs.ravel(order="F")

        # 5. Профиль прозрачности и кастомная палитра настоящего пламени 🔥
        # Первые элементы (черный цвет фона) занулены, чтобы куб растворился на белом фоне
        fire_colors = ["#000000", "#1f0600", "#5c0c00", "#bf2a00", "#ff6a00", "#ffb700", "#ffee99", "#ffffff"]
        base_opacity = np.array([0.0, 0.02, 0.10, 0.35, 0.65, 0.85, 0.95, 1.0])
        dynamic_opacity = base_opacity * opacity_factor

        # 6. Отрисовка объема на GPU
        self.plotter.add_volume(
            grid_gpu,
            scalars="Field",
            cmap=fire_colors,
            opacity=list(dynamic_opacity),
            shade=True,
            name="toroidal_fire_plasma_volume",
            show_scalar_bar=False
        )

        # 7. Настройка внутреннего свечения раскаленного газа
        volume_actor = self.plotter.renderer.actors["toroidal_fire_plasma_volume"]
        prop = volume_actor.GetProperty()
        prop.SetAmbient(ambient_value)      # Эффект самосвечения
        prop.SetDiffuse(1.0 - ambient_value) # Рассеивание света

        self.plotter.render()

    def closeEvent(self, event):
        self.plotter.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
