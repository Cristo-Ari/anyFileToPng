import sys
import os
import struct
import zlib
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QMessageBox
from PyQt5.QtCore import Qt

def build_png_chunk_with_type_and_data(chunk_type_bytes, chunk_data_bytes):
    chunk_length = len(chunk_data_bytes)
    chunk_length_bytes = struct.pack(">I", chunk_length)
    crc_value = zlib.crc32(chunk_type_bytes + chunk_data_bytes) & 0xffffffff
    crc_bytes = struct.pack(">I", crc_value)
    return chunk_length_bytes + chunk_type_bytes + chunk_data_bytes + crc_bytes

def create_png_file_bytes_from_original_filename_and_binary_data(original_filename, original_file_binary_data):
    png_signature = b'\x89PNG\r\n\x1a\n'
    image_width = 1
    image_height = 1
    bit_depth = 8
    color_type = 2
    compression_method = 0
    filter_method = 0
    interlace_method = 0
    ihdr_data = struct.pack(">IIBBBBB", image_width, image_height, bit_depth, color_type, compression_method, filter_method, interlace_method)
    ihdr_chunk = build_png_chunk_with_type_and_data(b'IHDR', ihdr_data)
    raw_image_row = b'\x00' + bytes([255, 255, 255])
    compressed_image_data = zlib.compress(raw_image_row)
    idat_chunk = build_png_chunk_with_type_and_data(b'IDAT', compressed_image_data)
    original_filename_bytes = original_filename.encode("utf-8")
    file_name_length_bytes = struct.pack(">I", len(original_filename_bytes))
    file_chunk_data = file_name_length_bytes + original_filename_bytes + original_file_binary_data
    file_custom_chunk = build_png_chunk_with_type_and_data(b'fiLe', file_chunk_data)
    iend_chunk = build_png_chunk_with_type_and_data(b'IEND', b'')
    return png_signature + ihdr_chunk + idat_chunk + file_custom_chunk + iend_chunk

def extract_original_file_from_png_file(png_file_path):
    with open(png_file_path, "rb") as png_file_object:
        png_file_bytes = png_file_object.read()
    png_signature = b'\x89PNG\r\n\x1a\n'
    if not png_file_bytes.startswith(png_signature):
        raise ValueError("File does not start with valid PNG signature")
    current_offset = len(png_signature)
    extracted_original_filename = None
    extracted_original_file_binary_data = None
    while current_offset < len(png_file_bytes):
        if current_offset + 8 > len(png_file_bytes):
            break
        chunk_length = struct.unpack(">I", png_file_bytes[current_offset:current_offset + 4])[0]
        current_offset += 4
        chunk_type = png_file_bytes[current_offset:current_offset + 4]
        current_offset += 4
        chunk_data = png_file_bytes[current_offset:current_offset + chunk_length]
        current_offset += chunk_length
        current_offset += 4
        if chunk_type == b'fiLe':
            if len(chunk_data) < 4:
                raise ValueError("Invalid custom chunk format")
            original_filename_length = struct.unpack(">I", chunk_data[0:4])[0]
            if len(chunk_data) < 4 + original_filename_length:
                raise ValueError("Invalid custom chunk format for filename")
            original_filename_bytes = chunk_data[4:4 + original_filename_length]
            extracted_original_filename = original_filename_bytes.decode("utf-8", errors="replace")
            extracted_original_file_binary_data = chunk_data[4 + original_filename_length:]
            break
    if extracted_original_filename is None or extracted_original_file_binary_data is None:
        raise ValueError("No embedded file found in PNG")
    return extracted_original_filename, extracted_original_file_binary_data

class DragAndDropConversionWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.instruction_label = QLabel("Drag and drop any file here to convert it to a PNG image or back to the original file.")
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.layout_container = QVBoxLayout()
        self.layout_container.addWidget(self.instruction_label)
        self.setLayout(self.layout_container)

    def dragEnterEvent(self, event_object):
        if event_object.mimeData().hasUrls():
            event_object.acceptProposedAction()
        else:
            event_object.ignore()

    def dropEvent(self, event_object):
        urls_list = event_object.mimeData().urls()
        if not urls_list:
            return
        for file_url in urls_list:
            file_path = file_url.toLocalFile()
            if not os.path.isfile(file_path):
                continue
            file_extension_lowercase = os.path.splitext(file_path)[1].lower()
            try:
                if file_extension_lowercase == ".png":
                    original_filename, original_file_binary_data = extract_original_file_from_png_file(file_path)
                    output_file_directory = os.path.dirname(file_path)
                    output_file_path = os.path.join(output_file_directory, "extracted_" + original_filename)
                    counter_for_existing = 1
                    base_output_file_path = output_file_path
                    while os.path.exists(output_file_path):
                        output_file_path = f"{os.path.splitext(base_output_file_path)[0]}_{counter_for_existing}{os.path.splitext(base_output_file_path)[1]}"
                        counter_for_existing += 1
                    with open(output_file_path, "wb") as output_file_object:
                        output_file_object.write(original_file_binary_data)
                    QMessageBox.information(self, "Conversion Successful", f"PNG converted back to file successfully:\n{output_file_path}")
                else:
                    with open(file_path, "rb") as input_file_object:
                        original_file_binary_data = input_file_object.read()
                    original_filename = os.path.basename(file_path)
                    png_file_bytes = create_png_file_bytes_from_original_filename_and_binary_data(original_filename, original_file_binary_data)
                    output_file_directory = os.path.dirname(file_path)
                    output_file_path = os.path.join(output_file_directory, original_filename + ".png")
                    counter_for_existing = 1
                    base_output_file_path = output_file_path
                    while os.path.exists(output_file_path):
                        output_file_path = f"{os.path.splitext(base_output_file_path)[0]}_{counter_for_existing}.png"
                        counter_for_existing += 1
                    with open(output_file_path, "wb") as output_file_object:
                        output_file_object.write(png_file_bytes)
                    QMessageBox.information(self, "Conversion Successful", f"File converted to PNG successfully:\n{output_file_path}")
            except Exception as exception_error:
                QMessageBox.critical(self, "Conversion Error", f"An error occurred:\n{str(exception_error)}")

class FileToPngConverterMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File to PNG Converter")
        self.setGeometry(100, 100, 600, 200)
        self.conversion_drag_and_drop_widget = DragAndDropConversionWidget()
        self.setCentralWidget(self.conversion_drag_and_drop_widget)

def main():
    application_instance = QApplication(sys.argv)
    main_window_instance = FileToPngConverterMainWindow()
    main_window_instance.show()
    sys.exit(application_instance.exec_())

if __name__ == "__main__":
    main()
