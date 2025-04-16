from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea, QPushButton, QFileDialog, QMessageBox


class SQLFileViewer(QDialog):
    def __init__(self, parent=None):
        """
        Initialise la fenêtre de visualisation du fichier SQL.
        """
        super().__init__(parent)
        self.setWindowTitle("Visualisation du fichier itv.sql")
        self.resize(800, 600)

        # Layout principal
        layout = QVBoxLayout(self)

        # Zone de défilement
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QLabel(self)
        self.scroll_content.setWordWrap(True)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        # Bouton pour charger un fichier
        self.load_button = QPushButton("Charger un fichier SQL", self)
        self.load_button.clicked.connect(self.load_sql_file)
        layout.addWidget(self.load_button)

    def load_sql_file(self):
        """
        Charge le contenu d'un fichier SQL sélectionné par l'utilisateur et l'affiche dans la zone de défilement.
        """
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un fichier SQL", "", "SQL Files (*.sql);;Tous les fichiers (*)", options=options
        )

        if not file_path:
            QMessageBox.warning(self, "Aucun fichier sélectionné", "Veuillez sélectionner un fichier pour continuer.")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                self.scroll_content.setText(content)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lire le fichier : {str(e)}")
