import os
from sqlite3 import OperationalError
from PyQt5.QtWidgets import QAction, QMainWindow, QTableWidgetItem, QFileDialog, QMessageBox
from qgis.PyQt.QtCore import Qt
from .itv_interface import Ui_selectFileButton  # Importer l'interface utilisateur
import psycopg2
from qgis.core import QgsVectorLayer, QgsProject
from qgis.gui import QgsMapCanvas
from .file_parser import FileParser
from qgis.core import QgsProviderRegistry, QgsSettings
from PyQt5.QtCore import QTimer


class ITVPluginMain:
    def __init__(self, iface):
        """Constructeur du plugin"""
        self.iface = iface
        self.window = None

    def initGui(self):
        """Initialise l'interface du plugin dans QGIS"""
        # Crée une action dans le menu pour ouvrir le plugin
        self.action = QAction("ITV Plugin QGIS", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        
        # Ajoute l'action au menu "Plugins" de QGIS
        self.iface.addPluginToMenu("&ITV Plugin QGIS", self.action)

    def unload(self):
        """Supprime le plugin du menu de QGIS"""
        self.iface.removePluginMenu("&ITV Plugin QGIS", self.action)

    def update_checkboxes(self):
        """
        Met à jour l'état des cases à cocher checkBox_pdf et checkBox_entreprise
        en fonction de l'entrée utilisateur dans pdfNameLineEdit et enterpriseNameLineEdit.
        """
        # Vérifie si l'utilisateur tape quelque chose dans pdfNameLineEdit
        self.ui.checkBox_pdf.setChecked(bool(self.ui.pdfNameLineEdit.text().strip()))

        # Vérifie si l'utilisateur tape quelque chose dans enterpriseNameLineEdit
        self.ui.checkBox_entreprise.setChecked(bool(self.ui.enterpriseNameLineEdit.text().strip()))

    def run(self):
        """Exécute l'interface de l'application"""
        # Crée une nouvelle fenêtre pour le plugin si elle n'existe pas encore
        if not self.window:
            self.window = QMainWindow()
            self.ui = Ui_selectFileButton()
            self.ui.setupUi(self.window)
            # Connecte le bouton de sélection de fichier et d'importation
            self.ui.pushButton.clicked.connect(self.select_file)
            self.ui.loadCollecteurButton.clicked.connect(self.select_collecteur_file)
            self.ui.loadRegardButton.clicked.connect(self.select_regard_file)
            self.ui.importButton.clicked.connect(self.test_database_connection)
            self.ui.importButton.clicked.connect(self.import_shapefile_collecteur)
            self.ui.importButton.clicked.connect(self.import_shapefile_regard)
            self.ui.importButton.clicked.connect(self.load_data_to_table)
            self.populate_database_connections()
            self.list_qgis_connections()  # Appeler la fonction pour remplir la liste déroulante
            self.ui.pushButton_testconnection.clicked.connect(self.test_selected_connection)
            self.ui.loadCollecteurButton_correspondance.clicked.connect(self.select_collecteur_correspondance_file)
            self.ui.loadRegardButton_correspondance.clicked.connect(self.select_regard_correspondance_file)
            self.ui.pdfNameLineEdit.textChanged.connect(self.update_checkboxes)
            self.ui.enterpriseNameLineEdit.textChanged.connect(self.update_checkboxes)

        
        # Affiche la fenêtre du plugin
        self.window.show()

    def select_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self.window, "Sélectionner le fichier TXT", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_path:
            self.ui.filePathLineEdit.setText(file_path)
            
            # Parse the file to extract metadata
            try:
                parser = FileParser()
                parsed_data = parser.parse(file_path)
                metadata = parsed_data.get("metadata", {})
                
                # Populate the dataPreviewTable with metadata
                self.ui.dataPreviewTable.setRowCount(len(metadata))
                self.ui.dataPreviewTable.setColumnCount(2)
                self.ui.dataPreviewTable.setHorizontalHeaderLabels(["Clé", "Valeur"])
                
                for row, (key, value) in enumerate(metadata.items()):
                    self.ui.dataPreviewTable.setItem(row, 0, QTableWidgetItem(key))
                    self.ui.dataPreviewTable.setItem(row, 1, QTableWidgetItem(str(value)))
                
                if metadata:
                    self.ui.checkBox_inspection.setChecked(True)  # Cocher la case si les métadonnées existent
                    self.log_message(f"Métadonnées chargées avec succès depuis le fichier : {file_path}")
                else:
                    self.ui.checkBox_inspection.setChecked(False)  # Décocher la case si aucune métadonnée
                    self.log_message(f"Aucune métadonnée trouvée dans le fichier : {file_path}")
            except Exception as e:
                self.ui.checkBox_inspection.setChecked(False)  # Décocher la case en cas d'erreur
                self.log_message(f"Erreur lors de l'extraction des métadonnées : {str(e)}")
        else:
            self.ui.checkBox_inspection.setChecked(False)  # Décocher la case si aucun fichier n'est sélectionné
            self.log_message("Aucun fichier sélectionné.")

    def select_collecteur_file(self):
        options = QFileDialog.Options()
        
        # Définir un filtre pour accepter uniquement les fichiers shapefile
        file_path_collecteur, _ = QFileDialog.getOpenFileName(self.window, "Sélectionner un fichier Shapefile Collecteur", "",
                                                "Shapefile (*.shp);;Tous les fichiers (*)", options=options)
        
        if file_path_collecteur:
            # Vérifier si le fichier est un shapefile valide
            if file_path_collecteur.endswith(".shp") and os.path.exists(file_path_collecteur):
                # Mettre à jour le QLineEdit (collecteurFilePathLabel) avec le chemin du fichier sélectionné
                self.ui.collecteurFilePathLabel.setText(file_path_collecteur)
                self.ui.checkBox_collecteurs.setChecked(True)  # Cocher la case si le fichier est valide
                self.log_message(f"Shapefile collecteur sélectionné : {file_path_collecteur}")
            else:
                self.ui.checkBox_collecteurs.setChecked(False)  # Décocher la case si le fichier n'est pas valide
                self.log_message(f"Erreur : Le fichier sélectionné n'est pas un shapefile valide : {file_path_collecteur}")
        else:
            self.ui.checkBox_collecteurs.setChecked(False)  # Décocher la case si aucun fichier n'est sélectionné
            self.log_message("Aucun fichier shapefile collecteur sélectionné.")

    def select_regard_file(self):
        options = QFileDialog.Options()
        
        # Définir un filtre pour accepter uniquement les fichiers shapefile
        file_path_regard, _ = QFileDialog.getOpenFileName(self.window, "Sélectionner un fichier Shapefile Regard", "",
                                                "Shapefile (*.shp);;Tous les fichiers (*)", options=options)
        
        if file_path_regard:
            # Vérifier si le fichier est un shapefile valide
            if file_path_regard.endswith(".shp") and os.path.exists(file_path_regard):
                # Mettre à jour le QLineEdit (regardFilePathLabel) avec le chemin du fichier sélectionné
                self.ui.regardFilePathLabel.setText(file_path_regard)
                self.ui.checkBox_regards.setChecked(True)  # Cocher la case si le fichier est valide
                self.log_message(f"Shapefile regard sélectionné : {file_path_regard}")
            else:
                self.ui.checkBox_regards.setChecked(False)  # Décocher la case si le fichier n'est pas valide
                self.log_message(f"Erreur : Le fichier sélectionné n'est pas un shapefile valide : {file_path_regard}")
        else:
            self.ui.checkBox_regards.setChecked(False)  # Décocher la case si aucun fichier shapefile regard sélectionné.

    def log_message(self, message):
        max_lines = 1000  # Nombre maximal de lignes de log
        self.ui.logTextEdit.append(message)  # Ajoute un message à la fin du QTextEdit
        
        # Supprime les lignes les plus anciennes si le nombre de lignes dépasse max_lines
        if len(self.ui.logTextEdit.toPlainText().splitlines()) > max_lines:
            cursor = self.ui.logTextEdit.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()

    def test_database_connection(self):
        """
        Teste la connexion à la base de données PostgreSQL sélectionnée et met à jour checkBox_connection.
        """
        try:
            # Récupérer les informations de connexion depuis l'interface utilisateur ou QgsSettings
            selected_connection = self.ui.comboBoxConnections.currentText()
            if not selected_connection:
                self.log_message("Erreur : Aucune connexion sélectionnée.")
                QMessageBox.critical(self.window, "Erreur", "Aucune connexion sélectionnée.")
                self.ui.checkBox_connection.setChecked(False)  # Décocher la case
                return

            settings = QgsSettings()
            prefix = f"PostgreSQL/connections/{selected_connection}/"

            dbname = settings.value(prefix + "database", "")
            user = self.ui.lineEditDatabaseUser.text() or settings.value(prefix + "username", "")
            password = self.ui.lineEditDatabasePassword.text() or settings.value(prefix + "password", "")
            host = settings.value(prefix + "host", "localhost")
            port = settings.value(prefix + "port", "5432")

            if not dbname or not user or not password:
                self.log_message("Erreur : Les informations de connexion sont incomplètes.")
                QMessageBox.critical(self.window, "Erreur", "Les informations de connexion sont incomplètes.")
                self.ui.checkBox_connection.setChecked(False)  # Décocher la case
                return

            # Tester la connexion avec psycopg2
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            self.log_message(f"Connexion réussie à la base de données '{dbname}' sur {host}:{port}.")
            self.ui.checkBox_connection.setChecked(True)  # Cocher la case
            conn.close()

        except psycopg2.OperationalError as e:
            self.log_message(f"Erreur de connexion : {str(e)}")
            QMessageBox.critical(self.window, "Erreur de connexion", f"Erreur de connexion : {str(e)}")
            self.ui.checkBox_connection.setChecked(False)  # Décocher la case
        except Exception as e:
            self.log_message(f"Erreur inattendue : {str(e)}")
            QMessageBox.critical(self.window, "Erreur inattendue", f"Erreur inattendue : {str(e)}")
            self.ui.checkBox_connection.setChecked(False)  # Décocher la case

    def import_shapefile_collecteur(self):
        shapefile_path_collecteur = self.ui.collecteurFilePathLabel.text()

        if shapefile_path_collecteur:
            # Vérifier si le fichier shapefile existe
            if os.path.exists(shapefile_path_collecteur):
                # Extraire le nom de la table à partir du fichier
                table_name = os.path.basename(shapefile_path_collecteur).split('.')[0]
                formatted_table_name = f"table_collecteur_{table_name}".replace(" ", "_").replace("-", "_").lower()
                if len(formatted_table_name) > 60:
                    formatted_table_name = formatted_table_name[:60]

                try:
                    # Récupérer les informations de connexion depuis l'interface utilisateur ou QgsSettings
                    selected_connection = self.ui.comboBoxConnections.currentText()
                    if not selected_connection:
                        self.log_message("Erreur : Aucune connexion sélectionnée.")
                        QMessageBox.critical(self.window, "Erreur", "Aucune connexion sélectionnée.")
                        return

                    settings = QgsSettings()
                    prefix = f"PostgreSQL/connections/{selected_connection}/"

                    dbname = settings.value(prefix + "database", "")
                    user = self.ui.lineEditDatabaseUser.text() or settings.value(prefix + "username", "")
                    password = self.ui.lineEditDatabasePassword.text() or settings.value(prefix + "password", "")
                    host = settings.value(prefix + "host", "localhost")
                    port = settings.value(prefix + "port", "5432")

                    if not dbname or not user or not password:
                        self.log_message("Erreur : Les informations de connexion sont incomplètes.")
                        QMessageBox.critical(self.window, "Erreur", "Les informations de connexion sont incomplètes.")
                        return

                    # Construire la commande ogr2ogr pour importer le shapefile dans le schéma itv
                    ogr2ogr_command = (
                        f'ogr2ogr -f "PostgreSQL" '
                        f'"PG:host={host} port={port} dbname={dbname} user={user} password={password}" '
                        f'"{shapefile_path_collecteur}" '
                        f'-lco GEOMETRY_NAME=geom -lco SCHEMA=itv -lco OVERWRITE=YES '
                        f'-nln {formatted_table_name} -lco precision=NO --config PG_USE_COPY NO'
                    )

                    # Exécuter la commande ogr2ogr
                    exit_code = os.system(ogr2ogr_command)
                    if exit_code == 0:
                        self.log_message(f"Shapefile {shapefile_path_collecteur} importé avec succès dans la table 'itv.{formatted_table_name}'.")
                        # Charger la table PostgreSQL comme couche dans QGIS
                        uri = f"dbname='{dbname}' host={host} port={port} user='{user}' password='{password}' table=\"itv\".\"{formatted_table_name}\" (geom)"
                        layer = QgsVectorLayer(uri, f"Collecteur - {formatted_table_name}", "postgres")
                        if layer.isValid():
                            QgsProject.instance().addMapLayer(layer)
                            self.log_message(f"Couche 'itv.{formatted_table_name}' ajoutée avec succès à QGIS.")
                        else:
                            self.log_message(f"Erreur : Impossible de charger la couche 'itv.{formatted_table_name}' dans QGIS.")
                    else:
                        self.log_message(f"Erreur lors de l'importation du shapefile {shapefile_path_collecteur}.")
                        QMessageBox.critical(self.window, "Erreur", f"Erreur lors de l'importation du shapefile {shapefile_path_collecteur}.")

                except Exception as e:
                    self.log_message(f"Erreur inattendue : {str(e)}")
                    QMessageBox.critical(self.window, "Erreur inattendue", f"Erreur inattendue : {str(e)}")
            else:
                self.log_message(f"Erreur : Le fichier shapefile {shapefile_path_collecteur} n'existe pas.")
        else:
            self.log_message("Erreur : Aucun fichier shapefile sélectionné.")

    def import_shapefile_regard(self):
        shapefile_path_regard = self.ui.regardFilePathLabel.text()

        if shapefile_path_regard:
            # Vérifier si le fichier shapefile existe
            if os.path.exists(shapefile_path_regard):
                # Extraire le nom de la table à partir du fichier
                table_name = os.path.basename(shapefile_path_regard).split('.')[0]
                formatted_table_name = f"table_regard_{table_name}".replace(" ", "_").replace("-", "_").lower()
                if len(formatted_table_name) > 60:
                    formatted_table_name = formatted_table_name[:60]

                try:
                    # Récupérer les informations de connexion depuis l'interface utilisateur ou QgsSettings
                    selected_connection = self.ui.comboBoxConnections.currentText()
                    if not selected_connection:
                        self.log_message("Erreur : Aucune connexion sélectionnée.")
                        QMessageBox.critical(self.window, "Erreur", "Aucune connexion sélectionnée.")
                        return

                    settings = QgsSettings()
                    prefix = f"PostgreSQL/connections/{selected_connection}/"

                    dbname = settings.value(prefix + "database", "")
                    user = self.ui.lineEditDatabaseUser.text() or settings.value(prefix + "username", "")
                    password = self.ui.lineEditDatabasePassword.text() or settings.value(prefix + "password", "")
                    host = settings.value(prefix + "host", "localhost")
                    port = settings.value(prefix + "port", "5432")

                    if not dbname or not user or not password:
                        self.log_message("Erreur : Les informations de connexion sont incomplètes.")
                        QMessageBox.critical(self.window, "Erreur", "Les informations de connexion sont incomplètes.")
                        return

                    # Construire la commande ogr2ogr pour importer le shapefile dans le schéma itv
                    ogr2ogr_command = (
                        f'ogr2ogr -f "PostgreSQL" '
                        f'"PG:host={host} port={port} dbname={dbname} user={user} password={password}" '
                        f'"{shapefile_path_regard}" '
                        f'-lco GEOMETRY_NAME=geom -lco SCHEMA=itv -lco OVERWRITE=YES '
                        f'-nln {formatted_table_name} -lco precision=NO --config PG_USE_COPY NO'
                    )

                    # Exécuter la commande ogr2ogr
                    exit_code = os.system(ogr2ogr_command)
                    if exit_code == 0:
                        self.log_message(f"Shapefile {shapefile_path_regard} importé avec succès dans la table 'itv.{formatted_table_name}'.")
                        # Charger la table PostgreSQL comme couche dans QGIS
                        uri = f"dbname='{dbname}' host={host} port={port} user='{user}' password='{password}' table=\"itv\".\"{formatted_table_name}\" (geom)"
                        layer = QgsVectorLayer(uri, f"Regard - {formatted_table_name}", "postgres")
                        if layer.isValid():
                            QgsProject.instance().addMapLayer(layer)
                            self.log_message(f"Couche 'itv.{formatted_table_name}' ajoutée avec succès à QGIS.")
                        else:
                            self.log_message(f"Erreur : Impossible de charger la couche 'itv.{formatted_table_name}' dans QGIS.")
                    else:
                        self.log_message(f"Erreur lors de l'importation du shapefile {shapefile_path_regard}.")
                        QMessageBox.critical(self.window, "Erreur", f"Erreur lors de l'importation du shapefile {shapefile_path_regard}.")

                except Exception as e:
                    self.log_message(f"Erreur inattendue : {str(e)}")
                    QMessageBox.critical(self.window, "Erreur inattendue", f"Erreur inattendue : {str(e)}")
            else:
                self.log_message(f"Erreur : Le fichier shapefile {shapefile_path_regard} n'existe pas.")
        else:
            self.log_message("Erreur : Aucun fichier shapefile sélectionné.")

    def insert_metadata_to_inspection(self, file_path, metadata):
        """
        Insère les métadonnées dans la table `itv.inspection` en utilisant la connexion configurée.
        """
        try:
            # Récupérer les informations de connexion depuis l'interface utilisateur ou QgsSettings
            selected_connection = self.ui.comboBoxConnections.currentText()
            if not selected_connection:
                self.log_message("Erreur : Aucune connexion sélectionnée.")
                QMessageBox.critical(self.window, "Erreur", "Aucune connexion sélectionnée.")
                return None

            settings = QgsSettings()
            prefix = f"PostgreSQL/connections/{selected_connection}/"

            dbname = settings.value(prefix + "database", "")
            user = self.ui.lineEditDatabaseUser.text() or settings.value(prefix + "username", "")
            password = self.ui.lineEditDatabasePassword.text() or settings.value(prefix + "password", "")
            host = settings.value(prefix + "host", "localhost")
            port = settings.value(prefix + "port", "5432")

            if not dbname or not user or not password:
                self.log_message("Erreur : Les informations de connexion sont incomplètes.")
                QMessageBox.critical(self.window, "Erreur", "Les informations de connexion sont incomplètes.")
                return None

            # Connexion à PostgreSQL
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            cursor = conn.cursor()

            # Requête SQL pour insérer les métadonnées
            query = """
                INSERT INTO itv.inspection (
                    gid, file, "A1", "A2", "A3", "A4", "A5", "A6", shp_reg, shp_coll,
                    entreprise, pdf_filename, shp_reg_table, shp_coll_table, created_by
                ) VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING gid;
            """

            # Récupérer les noms des fichiers shapefile et autres champs
            shp_coll = os.path.basename(self.ui.collecteurFilePathLabel.text()) if self.ui.collecteurFilePathLabel.text() else None
            shp_reg = os.path.basename(self.ui.regardFilePathLabel.text()) if self.ui.regardFilePathLabel.text() else None
            shp_coll_table = f"table_collecteur_{os.path.basename(self.ui.collecteurFilePathLabel.text()).split('.')[0].replace(' ', '_').replace('-', '_').lower()}" if self.ui.collecteurFilePathLabel.text() else None
            if len(shp_coll_table) > 60:
                shp_coll_table = shp_coll_table[:60]
            shp_reg_table = f"table_regard_{os.path.basename(self.ui.regardFilePathLabel.text()).split('.')[0].replace(' ', '_').replace('-', '_').lower()}" if self.ui.regardFilePathLabel.text() else None
            if len(shp_reg_table) > 60:
                shp_reg_table = shp_reg_table[:60]
            pdf_filename = self.ui.pdfNameLineEdit.text() if self.ui.pdfNameLineEdit.text() else None
            enterprise_name = self.ui.enterpriseNameLineEdit.text() if self.ui.enterpriseNameLineEdit.text() else None

            # Préparation des valeurs à insérer
            values = (
                file_path,  # Nom du fichier
                metadata.get("charset"),  # A1
                metadata.get("language"),  # A2
                metadata.get("delimiter"),  # A3
                metadata.get("decimalSeparator"),  # A4
                metadata.get("quoteChar"),  # A5
                metadata.get("version"),  # A6
                shp_reg,  # Nom du fichier shapefile regard
                shp_coll,  # Nom du fichier shapefile collecteur
                enterprise_name,  # Nom de l'entreprise
                pdf_filename,  # Nom du fichier PDF
                shp_reg_table,  # Nom de la table shp_reg
                shp_coll_table,  # Nom de la table shp_coll
                1  # created_by (exemple)
            )

            # Exécution de la requête
            cursor.execute(query, values)
            inspection_gid = cursor.fetchone()[0]  # Récupère l'ID généré

            # Validation des changements
            conn.commit()

            # Fermeture de la connexion
            cursor.close()
            conn.close()

            # Log de succès
            self.log_message(f"Métadonnées insérées avec succès dans la table `inspection` avec gid={inspection_gid}.")
            return inspection_gid

        except psycopg2.OperationalError as e:
            self.log_message(f"Erreur de connexion : {str(e)}")
            QMessageBox.critical(self.window, "Erreur de connexion", f"Erreur de connexion : {str(e)}")
        except psycopg2.Error as e:
            self.log_message(f"Erreur SQL : {str(e)}")
            QMessageBox.critical(self.window, "Erreur SQL", f"Erreur SQL : {str(e)}")
        except Exception as e:
            self.log_message(f"Erreur inattendue : {str(e)}")
            QMessageBox.critical(self.window, "Erreur inattendue", f"Erreur inattendue : {str(e)}")
        return None

    def insert_passages_to_inspection(self, inspection_gid, passages):
        """
        Insère les passages dans la table `itv.passage` pour une inspection donnée en utilisant la connexion configurée.
        """
        try:
            # Récupérer les informations de connexion depuis l'interface utilisateur ou QgsSettings
            selected_connection = self.ui.comboBoxConnections.currentText()
            if not selected_connection:
                self.log_message("Erreur : Aucune connexion sélectionnée.")
                return

            settings = QgsSettings()
            prefix = f"PostgreSQL/connections/{selected_connection}/"

            dbname = settings.value(prefix + "database", "")
            user = self.ui.lineEditDatabaseUser.text() or settings.value(prefix + "username", "")
            password = self.ui.lineEditDatabasePassword.text() or settings.value(prefix + "password", "")
            host = settings.value(prefix + "host", "localhost")
            port = settings.value(prefix + "port", "5432")

            if not dbname or not user or not password:
                self.log_message("Erreur : Les informations de connexion sont incomplètes.")
                return

            # Connexion à PostgreSQL
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            cursor = conn.cursor()

            # Requête SQL pour insérer les passages
            passage_query = """
                INSERT INTO itv.passage (
                    gid, n_passage, inspection_gid
                ) VALUES (DEFAULT, %s, %s)
                RETURNING gid;
            """

            # Insérer chaque passage
            for passage in passages:
                n_passage = passage["n_passage"]
                cursor.execute(passage_query, (n_passage, inspection_gid))
                passage_gid = cursor.fetchone()[0]  # Récupère l'ID généré pour le passage
                self.log_message(f"Passage {n_passage} inséré avec succès dans la table `passage` avec gid={passage_gid}.")

                # Insérer les données des tables associées au passage si elles existent
                if "tables" in passage:
                    if "#B01" in passage["tables"]:
                        b01_data = passage["tables"]["#B01"]
                        self.insert_b01_table(cursor, passage_gid, b01_data)
                    if "#B02" in passage["tables"]:
                        b02_data = passage["tables"]["#B02"]
                        self.insert_b02_table(cursor, passage_gid, b02_data)
                    if "#B03" in passage["tables"]:
                        b03_data = passage["tables"]["#B03"]
                        self.insert_b03_table(cursor, passage_gid, b03_data)
                    if "#B04" in passage["tables"]:
                        b04_data = passage["tables"]["#B04"]
                        self.insert_b04_table(cursor, passage_gid, b04_data)
                    if "#C" in passage["tables"]:
                        c_data = passage["tables"]["#C"]
                        self.insert_c_table(cursor, passage_gid, c_data)

            # Validation des changements
            conn.commit()

            # Fermeture de la connexion
            cursor.close()
            conn.close()

        except Exception as e:
            # Gestion des erreurs
            self.log_message(f"Erreur lors de l'insertion des passages : {str(e)}")

    def insert_b01_table(self, cursor, passage_gid, b01_data):
        self.log_message("Insertion des données B01 dans la table `B01`...")
        """
        Insère les données de la table `B01` associées à un passage dans la base de données.
        """
        try:
            b01_query = """
                INSERT INTO itv."B01" (
                    gid, "AAA", "AAB", "AAC", "AAD", "AAE", "AAF", "AAG", "AAH", "AAI", "AAJ", "AAK", "AAL", "AAM", "AAN", "AAO", "AAP", "AAQ", "AAT", "AAU", "AAV", passage_gid
                ) VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING gid;
            """
            expected_columns = ["AAA", "AAB", "AAC", "AAD", "AAE", "AAF", "AAG", "AAH", "AAI", "AAJ", "AAK", "AAL", "AAM", "AAN", "AAO", "AAP", "AAQ", "AAT", "AAU", "AAV"]
            parsed_columns = b01_data["columns"]
            column_index_map = {col: parsed_columns.index(col) for col in parsed_columns if col in expected_columns}

            for row in b01_data["rows"]:
                values = [
                    row[column_index_map[col]] if col in column_index_map else None
                    for col in expected_columns
                ]

                values.append(passage_gid)
                cursor.execute(b01_query, values)
                b01_gid = cursor.fetchone()[0] 
                self.log_message(f"Données B01 insérées avec succès dans la table `B01` avec gid={b01_gid}.")

        except Exception as e:
            # Gestion des erreurs
            self.log_message(f"Erreur lors de l'insertion des données B01 : {str(e)}")

    def insert_b02_table(self, cursor, passage_gid, b02_data):
        """
        Insère les données de la table `B02` associées à un passage dans la base de données.
        """
        try:
            # Requête SQL pour insérer les données de la table `B02`
            b02_query = """
                INSERT INTO itv."B02"(
                    gid, "ABA", "ABB", "ABC", "ABD", "ABE", "ABF", "ABG", "ABH", "ABI", "ABJ", "ABK", "ABL", "ABM", "ABN", "ABO", "ABP", "ABQ", "ABR", "ABS", "ABT", passage_gid)
                    VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING gid;
            """
            expected_columns = ["ABA", "ABB", "ABC", "ABD", "ABE", "ABF", "ABG", "ABH", "ABI", "ABJ", "ABK", "ABL", "ABM", "ABN", "ABO", "ABP", "ABQ", "ABR", "ABS", "ABT"]
            parsed_columns = b02_data["columns"]
            column_index_map = {col: parsed_columns.index(col) for col in parsed_columns if col in expected_columns}
            for row in b02_data["rows"]:
                values = [
                    row[column_index_map[col]] if col in column_index_map else None
                    for col in expected_columns
                ]
                values.append(passage_gid)
                cursor.execute(b02_query, values)
                b02_gid = cursor.fetchone()[0]
                self.log_message(f"Données B02 insérées avec succès dans la table `B02` avec gid={b02_gid}.")
        except Exception as e:
            self.log_message(f"Erreur lors de l'insertion des données B02 : {str(e)}")
        
    def insert_b03_table(self, cursor, passage_gid, b03_data):
        """
        Insère les données de la table `B03` associées à un passage dans la base de données.
        """
        try:
            # Requête SQL pour insérer les données de la table `B03`
            b03_query = """
                INSERT INTO itv."B03"(gid, "ACA", "ACB", "ACC", "ACD", "ACE", "ACF", "ACG", "ACH", "ACI", "ACJ", "ACK", "ACL", "ACM", "ACN", passage_gid)
	          VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING gid;
            """
            expected_columns = ["ACA", "ACB", "ACC", "ACD", "ACE", "ACF", "ACG", "ACH", "ACI", "ACJ", "ACK", "ACL", "ACM", "ACN"]
            parsed_columns = b03_data["columns"]
            column_index_map = {col: parsed_columns.index(col) for col in parsed_columns if col in expected_columns}
            for row in b03_data["rows"]:
                values = [
                    row[column_index_map[col]] if col in column_index_map else None
                    for col in expected_columns
                ]
                values.append(passage_gid)
                cursor.execute(b03_query, values)
                b03_gid = cursor.fetchone()[0]
                self.log_message(f"Données B03 insérées avec succès dans la table `B03` avec gid={b03_gid}.")
        except Exception as e:
            self.log_message(f"Erreur lors de l'insertion des données B03 : {str(e)}")
   
    def insert_b04_table(self, cursor, passage_gid, b04_data):
        """
        Insère les données de la table 'B04' associées à un passage dans la base de données.
        """
        try:
            # Requête SQL pour insérer les données de la table `B04`
            b04_query = """
            INSERT INTO itv."B04"(gid, "ADA", "ADB", "ADC", "ADD", "ADE", passage_gid)
                VALUES (DEFAULT, %s, %s, %s, %s, %s, %s)
                RETURNING gid;
            """
            expected_columns = ["ADA", "ADB", "ADC", "ADD", "ADE"]
            parsed_columns = b04_data["columns"]
            column_index_map = {col: parsed_columns.index(col) for col in parsed_columns if col in expected_columns}
            for row in b04_data["rows"]:
                values = [
                    row[column_index_map[col]] if col in column_index_map else None
                    for col in expected_columns
                ]
                values.append(passage_gid)
                cursor.execute(b04_query, values)
                b04_gid = cursor.fetchone()[0]
                self.log_message(f"Données B04 insérées avec succès dans la table `B04` avec gid={b04_gid}.")
        except Exception as e:
            self.log_message(f"Erreur lors de l'insertion des données B04 : {str(e)}")
        
    def insert_c_table(self, cursor, passage_gid, c_data):
        """
        Insère les données de la table `C` associées à un passage dans la base de données.
        """
        try:
            # Requête SQL pour insérer les données de la table `C`
            c_query = """
                INSERT INTO itv."C" (
                    gid, "I", "J", "A", "B", "C", "D", "E", "F", "G", "H", "K", "L", "M", "N", passage_gid
                ) VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING gid;
            """

            # Liste des colonnes attendues dans la table `C`
            expected_columns = ["I", "J", "A", "B", "C", "D", "E", "F", "G", "H", "K", "L", "M", "N"]

            # Colonnes présentes dans les données parsées
            parsed_columns = c_data["columns"]

            # Mapping des colonnes parsées aux colonnes attendues
            column_index_map = {col: parsed_columns.index(col) for col in parsed_columns if col in expected_columns}

            # Insérer chaque ligne de données dans la table `C`
            for row in c_data["rows"]:
                values = [
                    row[column_index_map[col]] if col in column_index_map else None
                    for col in expected_columns
                ]

                # Ajouter `passage_gid` à la fin des valeurs
                values.append(passage_gid)
                # Exécuter la requête d'insertion
                cursor.execute(c_query, values)
                c_gid = cursor.fetchone()[0]  # Récupère l'ID généré pour la ligne
                self.log_message(f"Données C insérées avec succès dans la table `C` avec gid={c_gid} dans le passage {passage_gid}.")

        except Exception as e:
            # Gestion des erreurs
            self.log_message(f"Erreur lors de l'insertion des données C : {str(e)}")
        
    def update_progress_bar(self, value):
        """
        Met à jour la barre de progression avec la valeur spécifiée.
        """
        self.ui.progressBar.setValue(value)

    def reset_progress_bar(self):
        """
        Réinitialise la barre de progression à 0.
        """
        self.ui.progressBar.setValue(0)

    def load_data_to_table(self):
        """
        Charge les données extraites du fichier TXT dans le tableau et insère les métadonnées, passages et données B01 dans la base de données.
        Met à jour la barre de progression pendant le traitement.
        """
        file_path = self.ui.filePathLineEdit.text()
        # Réinitialise la barre de progression
        self.reset_progress_bar()

        # Vérifie si un fichier a été sélectionné
        if not file_path:
            self.log_message("Erreur : Veuillez sélectionner un fichier TXT avant de continuer.")
            QMessageBox.warning(self.window, "Erreur", "Veuillez sélectionner un fichier TXT avant de continuer.")
            return

        try:
            # Étape 1 : Parse le fichier TXT
            self.update_progress_bar(10)
            parser = FileParser()
            parsed_data = parser.parse(file_path)
            metadata = parsed_data["metadata"]
            passages = parsed_data["passages"]

            # Étape 2 : Insère les métadonnées
            self.update_progress_bar(30)
            inspection_gid = self.insert_metadata_to_inspection(file_path, metadata)

            if inspection_gid:
                self.log_message(f"Métadonnées insérées avec succès dans la table `inspection` (gid={inspection_gid}).")

                # Étape 3 : Insère les passages
                self.update_progress_bar(50)
                self.insert_passages_to_inspection(inspection_gid, passages)

                # Étape 4 : Exécute la fonction SQL après les imports
                self.update_progress_bar(60)
                self.execute_set_id_sig(inspection_gid)

                # Étape 5 : Affiche la vue v_inspection dans QGIS
                self.update_progress_bar(70)
                self.display_v_inspection_view(inspection_gid)
                
                self.update_progress_bar(80)
                self.display_v_itv_details_geom_view(inspection_gid)
                
                self.update_progress_bar(90)
                self.display_v_itv_details_bcht_view(inspection_gid)

                # Étape finale : Terminer la barre de progression
                self.update_progress_bar(100)
            else:
                self.log_message("Erreur lors de l'insertion des métadonnées.")

        except Exception as e:
            self.log_message(f"Erreur lors de la lecture du fichier : {str(e)}")
            QMessageBox.critical(self.window, "Erreur", f"Erreur lors de la lecture du fichier : {str(e)}")
            self.reset_progress_bar()

    def execute_set_id_sig(self, inspection_gid):
        """
        Exécute la fonction SQL `itv.set_id_sig` sur la base de données et diffuse un message de succès.
        """
        try:
            # Récupérer les informations de connexion depuis l'interface utilisateur ou QgsSettings
            selected_connection = self.ui.comboBoxConnections.currentText()
            if not selected_connection:
                self.log_message("Erreur : Aucune connexion sélectionnée.")
                QMessageBox.critical(self.window, "Erreur", "Aucune connexion sélectionnée.")
                return

            settings = QgsSettings()
            prefix = f"PostgreSQL/connections/{selected_connection}/"

            dbname = settings.value(prefix + "database", "")
            user = self.ui.lineEditDatabaseUser.text() or settings.value(prefix + "username", "")
            password = self.ui.lineEditDatabasePassword.text() or settings.value(prefix + "password", "")
            host = settings.value(prefix + "host", "localhost")
            port = settings.value(prefix + "port", "5432")

            if not dbname or not user or not password:
                self.log_message("Erreur : Les informations de connexion sont incomplètes.")
                QMessageBox.critical(self.window, "Erreur", "Les informations de connexion sont incomplètes.")
                return

            # Connexion à PostgreSQL
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            cursor = conn.cursor()

            # Exécuter la fonction SQL
            sql_query = f"SELECT itv.set_id_sig({inspection_gid})"
            cursor.execute(sql_query)
            conn.commit()

            # Log de succès
            self.log_message("Mise à jour des correspondances effectuée avec succès.")
            # Diffuser un message de succès (simulé ici, car WS.broadcastToRoom n'est pas défini)
            ROOM_ID = "some_room_id"  # Remplacez par l'ID de la salle appropriée
            self.log_message(f"Diffusion au salon {ROOM_ID}: Mise à jour des correspondances effectuée avec succès.")

            # Fermeture de la connexion
            cursor.close()
            conn.close()

        except Exception as e:
            self.log_message(f"Erreur lors de l'exécution de la fonction SQL : {str(e)}")
            QMessageBox.critical(self.window, "Erreur", f"Erreur lors de l'exécution de la fonction SQL : {str(e)}")

    def populate_database_connections(self):
        """
        Remplit la comboBoxConnections avec les connexions PostgreSQL disponibles.
        """
        try:
            # Obtenir la liste des connexions PostgreSQL
            connections = QgsProviderRegistry.instance().providerMetadata("postgres").connections()
            self.ui.comboBoxConnections.clear()  # Effacer les éléments existants
            self.ui.comboBoxConnections.addItems(connections.keys())  # Ajouter les noms des connexions
            self.log_message("Sélectionnez une connexion pour afficher les paramètres.")
            self.ui.comboBoxConnections.currentIndexChanged.connect(self.log_selected_connection_params)

        except Exception as e:
            self.log_message(f"Erreur lors de la récupération des connexions PostgreSQL : {str(e)}")

    def log_selected_connection_params(self):
        """
        Affiche les paramètres de la connexion sélectionnée dans les logs en utilisant QgsSettings.
        Active les champs utilisateur et mot de passe si nécessaire.
        Met à jour checkBox_connection en fonction de la connexion.
        """
        try:
            selected_connection = self.ui.comboBoxConnections.currentText()
            if not selected_connection:
                self.log_message("Aucune connexion sélectionnée.")
                self.ui.checkBox_connection.setChecked(False)  # Décocher la case
                return

            # Utiliser QgsSettings pour récupérer les détails de la connexion
            settings = QgsSettings()
            prefix = f"PostgreSQL/connections/{selected_connection}/"

            dbname = settings.value(prefix + "database", "Non défini")
            user = settings.value(prefix + "username", "")
            password = settings.value(prefix + "password", "")
            host = settings.value(prefix + "host", "Non défini")
            port = settings.value(prefix + "port", "5432")  # Par défaut, port 5432

            # Tester la connexion
            try:
                conn = psycopg2.connect(
                    dbname=dbname,
                    user=user,
                    password=password,
                    host=host,
                    port=port
                )
                conn.close()
                self.ui.checkBox_connection.setChecked(True)  # Cocher la case
                self.log_message(f"Connexion réussie à la base de données '{dbname}' sur {host}:{port}.")
            except Exception:
                self.ui.checkBox_connection.setChecked(False)  # Décocher la case
                self.log_message(f"Impossible de se connecter à la base de données '{dbname}'.")

            # Afficher les informations de connexion dans les logs
            self.log_message(f"Connexion sélectionnée : {selected_connection}")
            self.log_message(f"Base de données : {dbname}")
            self.log_message(f"Utilisateur : {user if user else 'Non défini'}")
            self.log_message(f"Mot de passe : {'Défini' if password else 'Non défini'}")
            self.log_message(f"Hôte : {host}")
            self.log_message(f"Port : {port}")

            # Activer les champs utilisateur et mot de passe si vides
            if not user:
                self.ui.lineEditDatabaseUser.setEnabled(True)
                self.ui.lineEditDatabaseUser.setPlaceholderText("Entrez l'utilisateur")
                self.ui.lineEditDatabaseUser.clear()
            else:
                self.ui.lineEditDatabaseUser.setEnabled(False)
                self.ui.lineEditDatabaseUser.setText(user)

            if not password:
                self.ui.lineEditDatabasePassword.setEnabled(True)
                self.ui.lineEditDatabasePassword.setPlaceholderText("Entrez le mot de passe")
                self.ui.lineEditDatabasePassword.clear()
            else:
                self.ui.lineEditDatabasePassword.setEnabled(False)
                self.ui.lineEditDatabasePassword.setText(password)

        except Exception as e:
            self.log_message(f"Erreur lors de l'affichage des paramètres de connexion : {str(e)}")
            self.ui.checkBox_connection.setChecked(False)  # Décocher la case

    def list_qgis_connections(self):
        """
        Liste les connexions PostgreSQL configurées dans QGIS et les ajoute à la comboBoxConnections.
        """
        try:
            # Obtenir les connexions PostgreSQL enregistrées dans QGIS
            connections = QgsProviderRegistry.instance().providerMetadata("postgres").connections()
            self.ui.comboBoxConnections.clear()  # Effacer les éléments existants
            self.ui.comboBoxConnections.addItems(connections.keys())  # Ajouter les noms des connexions
            self.log_message("Connexions QGIS PostgreSQL listées avec succès.")
        except Exception as e:
            self.log_message(f"Erreur lors de la récupération des connexions QGIS : {str(e)}")

    def test_selected_connection(self):
        """
        Teste la connexion à la base de données PostgreSQL sélectionnée et met à jour checkBox_connection.
        """
        try:
            selected_connection = self.ui.comboBoxConnections.currentText()
            if not selected_connection:
                self.log_message("Erreur : Aucune connexion sélectionnée.")
                self.ui.checkBox_connection.setChecked(False)  # Décocher la case
                return

            # Récupérer les informations de connexion
            settings = QgsSettings()
            prefix = f"PostgreSQL/connections/{selected_connection}/"

            dbname = settings.value(prefix + "database", "")
            user = self.ui.lineEditDatabaseUser.text() or settings.value(prefix + "username", "")
            password = self.ui.lineEditDatabasePassword.text() or settings.value(prefix + "password", "")
            host = settings.value(prefix + "host", "localhost")
            port = settings.value(prefix + "port", "5432")

            if not dbname or not user or not password:
                self.log_message("Erreur : Les informations de connexion sont incomplètes.")
                self.ui.checkBox_connection.setChecked(False)  # Décocher la case
                return

            # Tester la connexion avec psycopg2
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            self.log_message(f"Connexion réussie à la base de données '{dbname}' sur {host}:{port}.")
            self.ui.checkBox_connection.setChecked(True)  # Cocher la case
            conn.close()

        except psycopg2.OperationalError as e:
            self.log_message(f"Erreur de connexion : {str(e)}")
            self.ui.checkBox_connection.setChecked(False)  # Décocher la case
        except Exception as e:
            self.log_message(f"Erreur inattendue : {str(e)}")
            self.ui.checkBox_connection.setChecked(False)  # Décocher la case

    def select_collecteur_correspondance_file(self):
        options = QFileDialog.Options()
        
        # Définir un filtre pour accepter uniquement les fichiers CSV
        file_path_collecteur_correspondance, _ = QFileDialog.getOpenFileName(
            self.window, 
            "Sélectionner un fichier CSV de correspondance Collecteur", 
            "", 
            "CSV Files (*.csv);;Tous les fichiers (*)", 
            options=options
        )
        
        if file_path_collecteur_correspondance:
            # Mettre à jour le QLineEdit (collecteurCorrespondanceFilePathLabel) avec le chemin du fichier sélectionné
            self.ui.collecteurCorrespondanceFilePathLabel.setText(file_path_collecteur_correspondance)
            self.log_message(f"Fichier CSV de correspondance collecteur sélectionné : {file_path_collecteur_correspondance}")

    def select_regard_correspondance_file(self):
        options = QFileDialog.Options()
        
        # Définir un filtre pour accepter uniquement les fichiers CSV
        file_path_regard_correspondance, _ = QFileDialog.getOpenFileName(
            self.window, 
            "Sélectionner un fichier CSV de correspondance Regard", 
            "", 
            "CSV Files (*.csv);;Tous les fichiers (*)", 
            options=options
        )
        
        if file_path_regard_correspondance:
            # Mettre à jour le QLineEdit (regardCorrespondanceFilePathLabel) avec le chemin du fichier sélectionné
            self.ui.regardCorrespondanceFilePathLabel.setText(file_path_regard_correspondance)
            self.log_message(f"Fichier CSV de correspondance regard sélectionné : {file_path_regard_correspondance}")

    def display_v_inspection_view(self, inspection_gid):
        """
        Affiche dans QGIS la vue SQL `itv.v_inspection` pour une inspection donnée.
        """
        try:
            # Récupérer les informations de connexion depuis l'interface utilisateur ou QgsSettings
            selected_connection = self.ui.comboBoxConnections.currentText()
            if not selected_connection:
                self.log_message("Erreur : Aucune connexion sélectionnée.")
                QMessageBox.critical(self.window, "Erreur", "Aucune connexion sélectionnée.")
                return

            settings = QgsSettings()
            prefix = f"PostgreSQL/connections/{selected_connection}/"

            dbname = settings.value(prefix + "database", "")
            user = self.ui.lineEditDatabaseUser.text() or settings.value(prefix + "username", "")
            password = self.ui.lineEditDatabasePassword.text() or settings.value(prefix + "password", "")
            host = settings.value(prefix + "host", "localhost")
            port = settings.value(prefix + "port", "5432")

            if not dbname or not user or not password:
                self.log_message("Erreur : Les informations de connexion sont incomplètes.")
                QMessageBox.critical(self.window, "Erreur", "Les informations de connexion sont incomplètes.")
                return

            # Construire l'URI pour la vue SQL
            sql_query = f"(SELECT * FROM itv.v_inspection WHERE inspection_gid = {inspection_gid})"
            geom_column = "geom"  # Nom de la colonne géométrique
            srid = 2154  # Remplacez par le SRID correct
            primary_key = "inspection_gid"  # Utilisez le champ unique ajouté à la vue

            uri = (
                f"dbname='{dbname}' host={host} port={port} user='{user}' password='{password}' "
                f"key='{primary_key}' srid={srid} type=Polygon table=\"({sql_query})\" ({geom_column})"
            )

            # Charger la vue comme une couche dans QGIS
            layer_name = f"Inspection {inspection_gid} - v_inspection"
            layer = QgsVectorLayer(uri, layer_name, "postgres")
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                self.log_message(f"Vue 'itv.v_inspection' pour l'inspection {inspection_gid} ajoutée avec succès à QGIS.")
            else:
                self.log_message(f"Erreur : Impossible de charger la vue 'itv.v_inspection' pour l'inspection {inspection_gid} dans QGIS.")
                QMessageBox.critical(self.window, "Erreur", f"Impossible de charger la vue 'itv.v_inspection' pour l'inspection {inspection_gid} dans QGIS.")

        except Exception as e:
            self.log_message(f"Erreur inattendue lors de l'affichage de la vue : {str(e)}")
            QMessageBox.critical(self.window, "Erreur", f"Erreur inattendue : {str(e)}")

    def display_v_itv_details_geom_view(self, inspection_gid):
        """
        Affiche dans QGIS la vue SQL `itv.v_itv_details_geom` pour une inspection donnée.
        """
        try:
            # Récupérer les informations de connexion depuis l'interface utilisateur ou QgsSettings
            selected_connection = self.ui.comboBoxConnections.currentText()
            if not selected_connection:
                self.log_message("Erreur : Aucune connexion sélectionnée.")
                QMessageBox.critical(self.window, "Erreur", "Aucune connexion sélectionnée.")
                return

            settings = QgsSettings()
            prefix = f"PostgreSQL/connections/{selected_connection}/"

            dbname = settings.value(prefix + "database", "")
            user = self.ui.lineEditDatabaseUser.text() or settings.value(prefix + "username", "")
            password = self.ui.lineEditDatabasePassword.text() or settings.value(prefix + "password", "")
            host = settings.value(prefix + "host", "localhost")
            port = settings.value(prefix + "port", "5432")

            if not dbname or not user or not password:
                self.log_message("Erreur : Les informations de connexion sont incomplètes.")
                QMessageBox.critical(self.window, "Erreur", "Les informations de connexion sont incomplètes.")
                return

            # Construire l'URI pour la vue SQL
            sql_query = f"(SELECT * FROM itv.v_itv_details_geom WHERE inspection_gid = {inspection_gid})"
            geom_column = "geom"  # Nom de la colonne géométrique
            srid = 2154  # Remplacez par le SRID correct
            primary_key = "gid"

            uri = (
                f"dbname='{dbname}' host={host} port={port} user='{user}' password='{password}' "
                f"key='{primary_key}' srid={srid} type=Point table=\"({sql_query})\" ({geom_column})"
            )

            # Charger la vue comme une couche dans QGIS
            layer_name = f"Details Geom {inspection_gid} - v_itv_details_geom"
            layer = QgsVectorLayer(uri, layer_name, "postgres")
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                self.log_message(f"Vue 'itv.v_itv_details_geom' pour l'inspection {inspection_gid} ajoutée avec succès à QGIS.")
            else:
                self.log_message(f"Erreur : Impossible de charger la vue 'itv.v_itv_details_geom' pour l'inspection {inspection_gid} dans QGIS.")
                QMessageBox.critical(self.window, "Erreur", f"Impossible de charger la vue 'itv.v_itv_details_geom' pour l'inspection {inspection_gid} dans QGIS.")

        except Exception as e:
            self.log_message(f"Erreur inattendue lors de l'affichage de la vue : {str(e)}")
            QMessageBox.critical(self.window, "Erreur", f"Erreur inattendue : {str(e)}")

    def display_v_itv_details_bcht_view(self, inspection_gid):
        """
        Affiche dans QGIS la vue SQL `itv.v_itv_details_bcht` pour une inspection donnée.
        """
        try:
            # Récupérer les informations de connexion depuis l'interface utilisateur ou QgsSettings
            selected_connection = self.ui.comboBoxConnections.currentText()
            if not selected_connection:
                self.log_message("Erreur : Aucune connexion sélectionnée.")
                QMessageBox.critical(self.window, "Erreur", "Aucune connexion sélectionnée.")
                return

            settings = QgsSettings()
            prefix = f"PostgreSQL/connections/{selected_connection}/"

            dbname = settings.value(prefix + "database", "")
            user = self.ui.lineEditDatabaseUser.text() or settings.value(prefix + "username", "")
            password = self.ui.lineEditDatabasePassword.text() or settings.value(prefix + "password", "")
            host = settings.value(prefix + "host", "localhost")
            port = settings.value(prefix + "port", "5432")

            if not dbname or not user or not password:
                self.log_message("Erreur : Les informations de connexion sont incomplètes.")
                QMessageBox.critical(self.window, "Erreur", "Les informations de connexion sont incomplètes.")
                return

            # Construire l'URI pour la vue SQL
            sql_query = f"(SELECT * FROM itv.v_itv_details_bcht WHERE inspection_gid = {inspection_gid})"
            geom_column = "geom"  # Nom de la colonne géométrique
            srid = 2154  # Remplacez par le SRID correct
            primary_key = "id"

            uri = (
                f"dbname='{dbname}' host={host} port={port} user='{user}' password='{password}' "
                f"key='{primary_key}' srid={srid} type=Point table=\"({sql_query})\" ({geom_column})"
            )

            # Charger la vue comme une couche dans QGIS
            layer_name = f"Details Bcht {inspection_gid} - v_itv_details_bcht"
            layer = QgsVectorLayer(uri, layer_name, "postgres")
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                self.log_message(f"Vue 'itv.v_itv_details_bcht' pour l'inspection {inspection_gid} ajoutée avec succès à QGIS.")
            else:
                self.log_message(f"Erreur : Impossible de charger la vue 'itv.v_itv_details_bcht' pour l'inspection {inspection_gid} dans QGIS.")
                QMessageBox.critical(self.window, "Erreur", f"Impossible de charger la vue 'itv.v_itv_details_bcht' pour l'inspection {inspection_gid} dans QGIS.")

        except Exception as e:
            self.log_message(f"Erreur inattendue lors de l'affichage de la vue : {str(e)}")
            QMessageBox.critical(self.window, "Erreur", f"Erreur inattendue : {str(e)}")
