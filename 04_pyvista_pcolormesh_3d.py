import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
import pyvista as pv
from pyvistaqt import QtInteractor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Аналоги pcolormesh в PyVista 3D")
        self.setGeometry(100, 100, 1200, 500)

        # Главный виджет интерфейса
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Создаем горизонтальный слой для трех независимых 3D-окон
        plotters_layout = QHBoxLayout()
        main_layout.addLayout(plotters_layout)

        # Инициализируем 3 отдельных плоттера PyVista
        self.plotters = [QtInteractor(self) for _ in range(3)]
        for p in self.plotters:
            plotters_layout.addWidget(p.interactor)

        # Кнопка для обновления данных (изменения фазы)
        self.btn = QPushButton("Случайный сдвиг фазы данных", self)
        self.btn.clicked.connect(self.update_plots)
        main_layout.addWidget(self.btn)

        self.update_plots()
        self.show()

    def update_plots(self):
        phase = np.random.uniform(0, np.pi)

        for p in self.plotters:
            p.clear()
            p.show_grid(color='gray', xtitle='X', ytitle='Y', ztitle='Z')

        # =====================================================================
        # ВАРИАНТ 1: Стандартная прямоугольная сетка (Рельеф функции)
        # =====================================================================
        x = np.linspace(-3, 3, 100)
        y = np.linspace(-3, 3, 100)
        X, Y = np.meshgrid(x, y)
        # Вычисляем Z (высоту рельефа)
        Z = np.exp(-X**2 - Y**2) * np.cos(2 * np.pi * X + phase)

        # В PyVista для создания StructuredGrid нужна матрица координат (X, Y, Z)
        grid1 = pv.StructuredGrid(X, Y, Z)
        # Записываем значения Z как массив данных (скаляры) для раскраски
        grid1.point_data["Values"] = Z.ravel(order="F")

        # Отображаем как 3D-поверхность с цветовой картой 'viridis'
        self.plotters[0].add_mesh(grid1, scalars="Values", cmap="viridis", show_edges=False)
        self.plotters[0].reset_camera()

        # =====================================================================
        # ВАРИАНТ 2: Искаженная сетка
        # =====================================================================
        x2 = np.logspace(0.1, 1, 50) - 1.0 # Сдвиг для наглядности
        y2 = np.linspace(-2, 2, 50)
        X2, Y2 = np.meshgrid(x2, y2)
        # Искажаем саму сетку (как в примере с matplotlib)
        X2 = X2 + 0.2 * np.sin(Y2 * 3)
        # Высота рельефа (масштабируем, чтобы Z не улетал в космос из-за cosh)
        Z2 = np.sin(X2 + phase) * np.cosh(y2 / 2)[:, None] * 0.3

        grid2 = pv.StructuredGrid(X2, Y2, Z2)
        grid2.point_data["Values"] = Z2.ravel(order="F")

        self.plotters[1].add_mesh(grid2, scalars="Values", cmap="plasma", show_edges=True)
        self.plotters[1].reset_camera()

        # =====================================================================
        # ВАРИАНТ 3: Полярная сетка (Круговой 3D-рельеф)
        # =====================================================================
        r = np.linspace(0, 3, 50) # Радиус
        theta = np.linspace(0, 2 * np.pi, 60) # Угол
        R, Theta = np.meshgrid(r, theta)

        # Переводим полярные координаты (R, Theta) в декартовы (X, Y) для 3D пространства
        X3 = R * np.cos(Theta)
        Y3 = R * np.sin(Theta)
        # Значения Z задают волны по кругу
        Z3 = (R * 0.3) * np.sin(3 * Theta + phase)

        grid3 = pv.StructuredGrid(X3, Y3, Z3)
        grid3.point_data["Values"] = Z3.ravel(order="F")

        self.plotters[2].add_mesh(grid3, scalars="Values", cmap="inferno", show_edges=False)
        self.plotters[2].reset_camera()

        # Запрашиваем перерисовку всех трех окон
        for p in self.plotters:
            p.render()

    def closeEvent(self, event):
        """Обязательно закрываем все плоттеры перед выходом!"""
        for p in self.plotters:
            p.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
