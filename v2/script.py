from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog
from PyQt5.QtGui import QImage, QDragEnterEvent, QDropEvent
from PyQt5.QtCore import Qt
import sys
import math


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Включаем поддержку drag and drop
        self.setAcceptDrops(True)

        # Создаем интерфейс
        self.layout = QVBoxLayout()
        self.button = QPushButton("Загрузить PNG и восстановить файл")
        self.button.clicked.connect(self.load_png)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)
        self.setWindowTitle("File to PNG Converter")

    def dragEnterEvent(self, event: QDragEnterEvent):
        # Принимаем событие, если перетаскивается файл
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragEnterEvent):
        # Подтверждаем перемещение файла
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        # Обрабатываем сброс файла
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.convert_to_png(file_path)

    def convert_to_png(self, file_path):
        # Читаем байты файла
        with open(file_path, 'rb') as f:
            file_bytes = f.read()

        # Добавляем размер файла (4 байта) в начало
        size = len(file_bytes)
        size_bytes = size.to_bytes(4, 'little')
        total_bytes = size_bytes + file_bytes

        # Определяем размеры изображения
        width = 256
        height = math.ceil(len(total_bytes) / width)

        # Создаем изображение в формате Grayscale8
        image = QImage(width, height, QImage.Format_Grayscale8)
        buffer = image.bits()
        buffer.setsize(image.byteCount())

        # Копируем данные в буфер изображения
        buffer[:len(total_bytes)] = total_bytes
        # Оставшиеся байты будут заполнены нулями автоматически

        # Сохраняем как PNG
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить PNG", "", "PNG files (*.png)"
        )
        if save_path:
            image.save(save_path, "PNG")
            print(f"Файл сохранен как {save_path}")

    def load_png(self):
        # Загружаем PNG
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть PNG", "", "PNG files (*.png)"
        )
        if file_path:
            # Читаем изображение
            image = QImage(file_path)
            buffer = image.bits()
            buffer.setsize(image.byteCount())

            # Извлекаем размер файла из первых 4 байтов
            size = int.from_bytes(buffer[:4], 'little')

            # Извлекаем байты файла
            file_bytes = buffer[4:4 + size]

            # Сохраняем восстановленный файл
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить восстановленный файл", "", "All files (*.*)"
            )
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(file_bytes)
                print(f"Файл восстановлен как {save_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())