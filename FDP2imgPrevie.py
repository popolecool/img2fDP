import sys
import os

def check_venv():
    if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
        print("ERREUR: L'application doit être exécutée dans l'environnement virtuel.")
        print("Veuillez utiliser 'python launch.py' pour démarrer l'application.")
        sys.exit(1)

check_venv()

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QProgressBar, QPushButton, QFileDialog, QScrollArea, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QImage
import sys
from fdp2img import image_to_hex, hex_to_image
import os
from PyQt6.QtGui import QPixmap
from PIL import ImageQt

class ConversionThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    
    def __init__(self, input_path, output_path, is_fdp, compress=False, skip_single=False, bw=False):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.is_fdp = is_fdp
        self.compress = compress
        self.skip_single = skip_single
        self.bw = bw

    def run(self):
        if self.is_fdp:
            hex_to_image(self.input_path, self.output_path)
        else:
            if self.bw:
                from PIL import Image
                img = Image.open(self.input_path)
                img = img.convert('L').convert('RGB')
                temp_path = self.input_path + '_temp.png'
                img.save(temp_path)
                
                image_to_hex(
                    temp_path, 
                    self.output_path, 
                    compress=self.compress
                )
                
                os.remove(temp_path)
            else:
                image_to_hex(
                    self.input_path, 
                    self.output_path, 
                    compress=self.compress
                )
            self.finished.emit()

class DropZone(QLabel):
    file_dropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(
            "<html><body>"
            "<p>Déposez votre fichier ici</p>"
            "<p>(image ou .fdp)</p>"
            "</body></html>"
        )
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                padding: 30px;
                background: #f0f0f0;
                min-height: 100px;
            }
        """)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_dropped.emit(files[0])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Convertisseur FDP universelle")
        self.setMinimumSize(800, 600)  # Fenêtre plus grande
        self.setAcceptDrops(True)  # Activer le drag and drop pour la fenêtre principale

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)  # Layout horizontal principal

        # Panel gauche pour le drop et les contrôle"s
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        layout.addWidget(left_panel)

        # Zone de drop
        self.drop_zone = DropZone()
        self.drop_zone.file_dropped.connect(self.preview_file)
        left_layout.addWidget(self.drop_zone)

        # Case à cocher pour la compression
        self.compress_checkbox = QCheckBox("Compresser l'image")
        left_layout.addWidget(self.compress_checkbox)

        # Ajouter les nouvelles cases à cocher après la case de compression existante
        self.skip_single_checkbox = QCheckBox("Ne pas compresser les pixels isolés")
        left_layout.addWidget(self.skip_single_checkbox)

        self.bw_checkbox = QCheckBox("Noir et blanc")
        self.bw_checkbox.stateChanged.connect(self.update_preview_bw)
        left_layout.addWidget(self.bw_checkbox)

        # Bouton de conversion
        self.convert_button = QPushButton("Convertir")
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setEnabled(False)
        left_layout.addWidget(self.convert_button)

        # Barre de progression et status
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.status_label)

        # Zone de prévisualisation avec scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        layout.setStretch(1, 2)  # Donne plus d'espace à la prévisualisation

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setWidget(self.preview_label)

        # Variables pour le zoom
        self.zoom_factor = 1.0
        self.current_pixmap = None
        self.current_file_path = None

        # Ajout des attributs pour maintenir les références
        self.temp_pil_image = None
        self.temp_qt_image = None

    def preview_file(self, file_path):
        self.current_file_path = file_path
        try:
            if file_path.lower().endswith('.fdp'):
                temp_img = hex_to_image(file_path, return_image=True)
                if temp_img is None:  # Si la conversion a échoué
                    self.status_label.setText("Erreur: Fichier FDP invalide ou corrompu")
                    return
                if temp_img:
                    self.temp_pil_image = temp_img
                    self.update_preview_with_filters()
            else:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    self.temp_pil_image = ImageQt.fromqpixmap(pixmap)
                    self.update_preview_with_filters()
                else:
                    self.status_label.setText("Erreur: Format d'image non supporté")

            self.convert_button.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"Erreur: {str(e)}")
            self.convert_button.setEnabled(False)

    def update_preview_with_filters(self):
        if self.temp_pil_image:
            # Appliquer le filtre noir et blanc si activé
            working_image = self.temp_pil_image
            if self.bw_checkbox.isChecked():
                working_image = working_image.convert('L').convert('RGB')
            
            # Convertir en QPixmap pour l'affichage
            qim = ImageQt.ImageQt(working_image)
            self.temp_qt_image = qim
            pixmap = QPixmap.fromImage(self.temp_qt_image)
            self.show_preview(pixmap)

    def update_preview_bw(self):
        self.update_preview_with_filters()

    def show_preview(self, pixmap_or_image):
        try:
            if isinstance(pixmap_or_image, QImage):
                pixmap = QPixmap.fromImage(pixmap_or_image)
            else:
                pixmap = pixmap_or_image
            
            if pixmap.width() > 0 and pixmap.height() > 0:
                self.current_pixmap = pixmap
                self.update_preview()
            else:
                self.status_label.setText("Erreur: Image invalide")
        except Exception as e:
            self.status_label.setText(f"Erreur: {str(e)}")

    def update_preview(self):
        if self.current_pixmap:
            # Redimensionner l'image pour remplir l'écran
            scaled_pixmap = self.current_pixmap.scaled(
                int(self.current_pixmap.width() * self.zoom_factor),
                int(self.current_pixmap.height() * self.zoom_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # S'assurer que l'image ne dépasse pas la taille originale
            if scaled_pixmap.width() > self.current_pixmap.width() * 2 or scaled_pixmap.height() > self.current_pixmap.height() * 2:
                scaled_pixmap = self.current_pixmap.scaled(
                    self.current_pixmap.width() * 2,
                    self.current_pixmap.height() * 2,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

            self.preview_label.setPixmap(scaled_pixmap)

    def wheelEvent(self, event):
        if self.current_pixmap:
            if event.angleDelta().y() > 0:
                self.zoom_factor *= 1.1
            else:
                self.zoom_factor /= 1.1
            
            # Limiter le zoom pour ne pas dépasser 2.0
            if self.zoom_factor > 2.0:
                self.zoom_factor = 2.0
            
            self.update_preview()

    def start_conversion(self):
        if not self.current_file_path:
            return

        filename, ext = os.path.splitext(self.current_file_path)
        is_fdp = ext.lower() == '.fdp'
        default_ext = 'Images (*.jpg)' if is_fdp else 'FDP Files (*.fdp)'
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer sous",
            filename + ('.jpg' if is_fdp else '.fdp'),
            default_ext
        )
        
        if output_path:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.status_label.setText("Conversion en cours...")
            
            compress = self.compress_checkbox.isChecked()
            skip_single = self.skip_single_checkbox.isChecked()
            bw = self.bw_checkbox.isChecked()
            
            self.conversion_thread = ConversionThread(
                self.current_file_path, 
                output_path, 
                is_fdp,
                compress=compress,
                skip_single=skip_single,
                bw=bw
            )
            self.conversion_thread.finished.connect(self.conversion_finished)
            self.conversion_thread.start()

    def conversion_finished(self):
        self.progress_bar.setVisible(False)
        self.status_label.setText("Conversion terminée!")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.preview_file(files[0])

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()