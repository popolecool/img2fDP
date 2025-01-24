import sys
import os
import multiprocessing


from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QProgressBar, QPushButton, QFileDialog, QScrollArea, QCheckBox,
                           QSlider, QDialog, QSplitter)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRectF, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QImage, QIcon, QPainter
import sys
from fdp2img import image_to_hex, hex_to_image
import os
from PyQt6.QtGui import QPixmap
from PIL import ImageQt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Réglages")
        layout = QVBoxLayout(self)
        
        # Calculer le nombre maximum de threads disponibles
        max_threads = multiprocessing.cpu_count() - 2
        if max_threads < 1:
            max_threads = 1
            
        # Label pour afficher le nombre de threads
        self.thread_label = QLabel(f"Nombre de threads: {parent.num_threads}")
        layout.addWidget(self.thread_label)
        
        # Slider pour ajuster le nombre de threads
        self.thread_slider = QSlider(Qt.Orientation.Horizontal)
        self.thread_slider.setMinimum(1)
        self.thread_slider.setMaximum(max_threads)
        self.thread_slider.setValue(parent.num_threads)
        self.thread_slider.valueChanged.connect(self.update_thread_label)
        layout.addWidget(self.thread_slider)
        
        # Bouton OK
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

    def update_thread_label(self, value):
        self.thread_label.setText(f"Nombre de threads: {value}")

class ConversionThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    
    def __init__(self, input_path, output_path, is_fdp, compress=False, skip_single=False, bw=False, num_threads=1):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.is_fdp = is_fdp
        self.compress = compress
        self.skip_single = skip_single
        self.bw = bw
        self.num_threads = num_threads

    def run(self):
        if self.is_fdp:
            hex_to_image(self.input_path, self.output_path, num_threads=self.num_threads)
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
                    compress=self.compress,
                    num_threads=self.num_threads
                )
                
                os.remove(temp_path)
            else:
                image_to_hex(
                    self.input_path, 
                    self.output_path, 
                    compress=self.compress,
                    num_threads=self.num_threads
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
                color: #000000;
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

class SecretDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("😍😍😍")
        self.setFixedSize(400, 400)
        
        layout = QVBoxLayout(self)
        
        # Label pour l'image
        image_label = QLabel()
        pixmap = QPixmap("fdp.png")  # Assurez-vous que l'image existe dans le dossier
        scaled_pixmap = pixmap.scaled(380, 380, Qt.AspectRatioMode.KeepAspectRatio, 
                                    Qt.TransformationMode.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Convertisseur FDP universelle")
        self.setMinimumSize(800, 600)
        
        # Détecter le thème du système
        style_hints = QApplication.instance().styleHints()
        self.is_dark_mode = style_hints.colorScheme() == Qt.ColorScheme.Dark
        self.setWindowIcon(QIcon("logo-d.png" if self.is_dark_mode else "logo-l.png"))
        
        # Créer le widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Créer le splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Créer le panel gauche
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)  # Marges réduites
        
        # Zone de drop avec taille minimale
        self.drop_zone = DropZone()
        self.drop_zone.setMinimumWidth(200)  # Largeur minimale
        left_layout.addWidget(self.drop_zone)
        
        # Conteneur pour les checkboxes
        checkbox_container = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_container)
        checkbox_layout.setSpacing(5)  # Espacement réduit
        
        # Ajouter les checkboxes
        self.compress_checkbox = QCheckBox("Compresser l'image")
        self.skip_single_checkbox = QCheckBox("Ne pas compresser les pixels isolés")
        self.bw_checkbox = QCheckBox("Noir et blanc")
        self.bw_checkbox.stateChanged.connect(self.update_preview_bw)
        
        checkbox_layout.addWidget(self.compress_checkbox)
        checkbox_layout.addWidget(self.skip_single_checkbox)
        checkbox_layout.addWidget(self.bw_checkbox)
        left_layout.addWidget(checkbox_container)
        
        # Boutons et barre de progression
        self.convert_button = QPushButton("Enregister l'image converti")
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setEnabled(False)
        left_layout.addWidget(self.convert_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)  # Permettre le retour à la ligne
        left_layout.addWidget(self.status_label)
        
        # Boutons du bas
        bottom_layout = QHBoxLayout()
        self.print_button = QPushButton("Imprimer")
        self.print_button.clicked.connect(self.print_image)
        self.print_button.setEnabled(False)
        
        settings_button = QPushButton("Paramètres")
        settings_button.clicked.connect(self.show_settings)
        
        bottom_layout.addWidget(self.print_button)
        bottom_layout.addWidget(settings_button)
        left_layout.addLayout(bottom_layout)
        
        # Ajouter un stretch pour pousser les widgets vers le haut
        left_layout.addStretch()
        
        # Créer le conteneur de prévisualisation
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(5, 5, 5, 5)
        
        # Scroll area pour la prévisualisation
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setWidget(self.preview_label)
        preview_layout.addWidget(scroll_area)
        
        # Ajouter les panels au splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(preview_container)
        
        # Définir les tailles initiales du splitter (30% - 70%)
        splitter.setSizes([300, 700])
        
        # Définir les tailles minimales
        left_panel.setMinimumWidth(200)
        preview_container.setMinimumWidth(400)
        
        # Appliquer le thème initial
        self.toggle_theme()

        # Variables pour le zoom
        self.zoom_factor = 1.0
        self.current_pixmap = None
        self.current_file_path = None

        # Ajout des attributs pour maintenir les références
        self.temp_pil_image = None
        self.temp_qt_image = None

        # Ajouter le nombre de threads par défaut
        self.num_threads = 1

        # Ajouter les variables pour la séquence de touches
        self.keys_pressed = set()
        self.secret_timer = QTimer()
        self.secret_timer.setSingleShot(True)
        self.secret_timer.timeout.connect(self.reset_keys)

        # Connecter le signal de drop_zone
        self.drop_zone.file_dropped.connect(self.preview_file)

    def preview_file(self, file_path):
        self.current_file_path = file_path
        try:
            if file_path.lower().endswith('.fdp'):
                temp_img = hex_to_image(file_path, return_image=True)
                if temp_img is None:
                    self.status_label.setText("Erreur: Fichier FDP invalide ou corrompu\nSi le problème persiste, veuillez ouvrir une issue sur https://github.com/popolecool/img2fDP/issues")
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
                    self.status_label.setText("Erreur: Format d'image non supporté\nSi le problème persiste, veuillez ouvrir une issue sur https://github.com/popolecool/img2fDP/issues")

            self.convert_button.setEnabled(True)
            self.print_button.setEnabled(True)
        except Exception as e:
            error_msg = (f"Erreur: {str(e)}\n"
                        "Si le problème persiste, veuillez ouvrir une issue sur\n"
                        "https://github.com/popolecool/img2fDP/issues\n"
                        "en incluant les détails de l'erreur ci-dessus.")
            self.status_label.setText(error_msg)
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
                bw=bw,
                num_threads=self.num_threads
            )
            self.conversion_thread.finished.connect(self.conversion_finished)
            try:
                self.conversion_thread.start()
            except Exception as e:
                error_msg = (f"Erreur de conversion: {str(e)}\n"
                            "Si le problème persiste, veuillez ouvrir une issue sur\n"
                            "https://github.com/popolecool/img2fDP/issues\n"
                            "en incluant les détails de l'erreur ci-dessus.")
                self.status_label.setText(error_msg)

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_M:
            self.toggle_theme()
        
        # Ajouter la touche à l'ensemble des touches pressées
        self.keys_pressed.add(event.key())
        self.secret_timer.start(500)  # Reset après 500ms
        
        # Vérifier la combinaison F + D + P
        if (Qt.Key.Key_F in self.keys_pressed and 
            Qt.Key.Key_D in self.keys_pressed and 
            Qt.Key.Key_P in self.keys_pressed):
            self.show_secret_dialog()
    
    def keyReleaseEvent(self, event):
        # Retirer la touche de l'ensemble quand elle est relâchée
        self.keys_pressed.discard(event.key())
    
    def reset_keys(self):
        # Réinitialiser l'ensemble des touches pressées
        self.keys_pressed.clear()
    
    def show_secret_dialog(self):
        dialog = SecretDialog(self)
        dialog.exec()

    def toggle_theme(self):
        if self.is_dark_mode:
            # Mode clair avec tons violets
            self.setStyleSheet("""
                QMainWindow, QDialog {
                    background-color: #F8F7FD;
                    color: #2D1674;
                }
                QLabel, QCheckBox {
                    color: #2D1674;
                }
                QPushButton {
                    background-color: #9F8FEF;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #8A77E8;
                }
                QPushButton:disabled {
                    background-color: #D5D0F2;
                    color: #8E89A3;
                }
                QProgressBar {
                    border: 1px solid #9F8FEF;
                    border-radius: 4px;
                    background-color: #F0EDFC;
                    color: #2D1674;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #9F8FEF;
                    border-radius: 3px;
                }
                QScrollArea, QSlider {
                    background-color: #F8F7FD;
                    border: 1px solid #D5D0F2;
                    border-radius: 4px;
                }
                QSlider::groove:horizontal {
                    background: #D5D0F2;
                    height: 4px;
                }
                QSlider::handle:horizontal {
                    background: #9F8FEF;
                    width: 16px;
                    margin: -6px 0;
                    border-radius: 8px;
                }
            """)
            self.is_dark_mode = False
            self.setWindowIcon(QIcon("logo-l.png"))
            self.preview_label.setStyleSheet("background-color: #FFFFFF; border: 1px solid #D5D0F2; border-radius: 4px;")
            self.drop_zone.setStyleSheet("""
                QLabel {
                    border: 2px dashed #9F8FEF;
                    border-radius: 5px;
                    padding: 30px;
                    background: #F0EDFC;
                    min-height: 100px;
                    color: #2D1674;
                }
            """)
        else:
            # Mode sombre avec tons violets
            self.setStyleSheet("""
                QMainWindow, QDialog {
                    background-color: #1A1525;
                    color: #E6E0FF;
                }
                QLabel, QCheckBox {
                    color: #E6E0FF;
                }
                QPushButton {
                    background-color: #6B4BDE;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #8666FF;
                }
                QPushButton:disabled {
                    background-color: #3D3459;
                    color: #9385BD;
                }
                QProgressBar {
                    border: 1px solid #6B4BDE;
                    border-radius: 4px;
                    background-color: #2D2139;
                    color: #E6E0FF;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #6B4BDE;
                    border-radius: 3px;
                }
                QScrollArea, QSlider {
                    background-color: #1A1525;
                    border: 1px solid #3D3459;
                    border-radius: 4px;
                }
                QSlider::groove:horizontal {
                    background: #3D3459;
                    height: 4px;
                }
                QSlider::handle:horizontal {
                    background: #6B4BDE;
                    width: 16px;
                    margin: -6px 0;
                    border-radius: 8px;
                }
            """)
            self.is_dark_mode = True
            self.setWindowIcon(QIcon("logo-d.png"))
            self.preview_label.setStyleSheet("background-color: #2D2139; border: 1px solid #3D3459; border-radius: 4px;")
            self.drop_zone.setStyleSheet("""
                QLabel {
                    border: 2px dashed #6B4BDE;
                    border-radius: 5px;
                    padding: 30px;
                    background: #2D2139;
                    min-height: 100px;
                    color: #E6E0FF;
                }
            """)

    def show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.num_threads = dialog.thread_slider.value()

    def print_image(self):
        if self.current_pixmap:
            printer = QPrinter()
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.handle_paint_request(printer)

    def handle_paint_request(self, printer):
        painter = QPainter(printer)
        
        # Obtenir les dimensions de la page
        page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
        
        # Calculer le ratio pour maintenir les proportions
        scale_w = page_rect.width() / self.current_pixmap.width()
        scale_h = page_rect.height() / self.current_pixmap.height()
        scale = min(scale_w, scale_h)
        
        # Calculer les nouvelles dimensions
        new_width = self.current_pixmap.width() * scale
        new_height = self.current_pixmap.height() * scale
        
        # Calculer les positions pour centrer l'image
        x = (page_rect.width() - new_width) / 2
        y = (page_rect.height() - new_height) / 2
        
        # Définir la zone de dessin
        target_rect = QRectF(x, y, new_width, new_height)
        source_rect = QRectF(0, 0, self.current_pixmap.width(), self.current_pixmap.height())
        
        # Dessiner l'image
        painter.drawPixmap(target_rect, self.current_pixmap, source_rect)
        painter.end()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()