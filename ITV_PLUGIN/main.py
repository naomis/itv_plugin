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

        
        # Affiche la fenêtre du plugin
        self.window.show()

    def select_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self.window, "Sélectionner le fichier TXT", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_path:
            self.ui.filePathLineEdit.setText(file_path)

    def select_collecteur_file(self):
        options = QFileDialog.Options()
        
        # Définir un filtre pour accepter uniquement les fichiers shapefile
        file_path_collecteur, _ = QFileDialog.getOpenFileName(self.window, "Sélectionner un fichier Shapefile Collecteur", "",
                                                "Shapefile (*.shp);;Tous les fichiers (*)", options=options)
        
        if file_path_collecteur:
            # Mettre à jour le QLineEdit (collecteurFilePathLabel) avec le chemin du fichier sélectionné
            self.ui.collecteurFilePathLabel.setText(file_path_collecteur)
            self.log_message(f"Shapefile collecteur sélectionné : {file_path_collecteur}")
               
    def select_regard_file(self):
        options = QFileDialog.Options()
        
        # Définir un filtre pour accepter uniquement les fichiers shapefile
        file_path_regard, _ = QFileDialog.getOpenFileName(self.window, "Sélectionner un fichier Shapefile Regard", "",
                                                "Shapefile (*.shp);;Tous les fichiers (*)", options=options)
        
        if file_path_regard:
            # Mettre à jour le QLineEdit (regardFilePathLabel) avec le chemin du fichier sélectionné
            self.ui.regardFilePathLabel.setText(file_path_regard)
            self.log_message(f"Shapefile regard sélectionné : {file_path_regard}")
       
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
        Teste la connexion à la base de données PostgreSQL sélectionnée et affiche le résultat dans log_message.
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

            # Tester la connexion avec psycopg2
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            self.log_message(f"Connexion réussie à la base de données '{dbname}' sur {host}:{port}.")
            QMessageBox.information(self.window, "Succès", f"Connexion réussie à la base de données '{dbname}' sur {host}:{port}.")
            conn.close()

        except psycopg2.OperationalError as e:
            self.log_message(f"Erreur de connexion : {str(e)}")
            QMessageBox.critical(self.window, "Erreur de connexion", f"Erreur de connexion : {str(e)}")
        except Exception as e:
            self.log_message(f"Erreur inattendue : {str(e)}")
            QMessageBox.critical(self.window, "Erreur inattendue", f"Erreur inattendue : {str(e)}")

    def import_shapefile_collecteur(self):
        shapefile_path_collecteur = self.ui.collecteurFilePathLabel.text()

        if shapefile_path_collecteur:
            # Vérifier si le fichier shapefile existe
            if os.path.exists(shapefile_path_collecteur):
                # Charger le shapefile dans QGIS
                layer = QgsVectorLayer(shapefile_path_collecteur, "Collecteur", "ogr")

                # Vérifier si la couche est valide
                if layer.isValid():
                    # Ajouter la couche au projet QGIS
                    QgsProject.instance().addMapLayer(layer)
                    self.log_message(f"Shapefile {shapefile_path_collecteur} chaé avec succès dans QGIS.")
                else:
                    self.log_message(f"Erreur : Impossible de charger le shapefile {shapefile_path_collecteur}.")
            else:
                self.log_message(f"Erreur : Le fichier shapefile {shapefile_path_collecteur} n'existe pas.")
        else:
            self.log_message("Erreur : Aucun fichier shapefile sélectionné.")
            
    def import_shapefile_regard(self):
            shapefile_path_regard = self.ui.regardFilePathLabel.text() 

            if shapefile_path_regard:
                # Vérifier si le fichier shapefile existe
                if os.path.exists(shapefile_path_regard):
                    # Charger le shapefile dans QGIS
                    layer = QgsVectorLayer(shapefile_path_regard, "Regard", "ogr")

                    # Vérifier si la couche est valide
                    if layer.isValid():
                        # Ajouter la couche au projet QGIS
                        QgsProject.instance().addMapLayer(layer)
                        self.log_message(f"Shapefile {shapefile_path_regard} chargé avec succès dans QGIS.")
                    else:
                        self.log_message(f"Erreur : Impossible de charger le shapefile {shapefile_path_regard}.")
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
            shp_coll_table = os.path.basename(self.ui.collecteurFilePathLabel.text()) if self.ui.collecteurFilePathLabel.text() else None
            shp_reg_table = os.path.basename(self.ui.regardFilePathLabel.text()) if self.ui.regardFilePathLabel.text() else None
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
                shp_reg_table,  # Nom du fichier shapefile regard
                shp_coll_table,  # Nom du fichier shapefile collecteur
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
            QMessageBox.information(self.window, "Succès", f"Métadonnées insérées avec succès dans la table `inspection` avec gid={inspection_gid}.")
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
        
    def load_data_to_table(self):
        """Charge les données extraites du fichier TXT dans le tableau et insère les métadonnées, passages et données B01 dans la base de données."""
        file_path = self.ui.filePathLineEdit.text()

        # Vérifie si un fichier a été sélectionné
        if not file_path:
            self.log_message("Erreur : Veuillez sélectionner un fichier TXT avant de continuer.")
            QMessageBox.warning(self.window, "Erreur", "Veuillez sélectionner un fichier TXT avant de continuer.")
            return

        try:
            # Parse le fichier TXT
            parser = FileParser()
            parsed_data = parser.parse(file_path)
            metadata = parsed_data["metadata"]
            passages = parsed_data["passages"]
            inspection_gid = self.insert_metadata_to_inspection(file_path, metadata)

            if inspection_gid:
                self.log_message(f"Métadonnées insérées avec succès dans la table `inspection` (gid={inspection_gid}).")
                self.insert_passages_to_inspection(inspection_gid, passages)
            else:
                self.log_message("Erreur lors de l'insertion des métadonnées.")

        except Exception as e:
            self.log_message(f"Erreur lors de la lecture du fichier : {str(e)}")
            QMessageBox.critical(self.window, "Erreur", f"Erreur lors de la lecture du fichier : {str(e)}")

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
        """
        try:
            selected_connection = self.ui.comboBoxConnections.currentText()
            if not selected_connection:
                self.log_message("Aucune connexion sélectionnée.")
                return

            # Utiliser QgsSettings pour récupérer les détails de la connexion
            settings = QgsSettings()
            prefix = f"PostgreSQL/connections/{selected_connection}/"

            dbname = settings.value(prefix + "database", "Non défini")
            user = settings.value(prefix + "username", "")
            password = settings.value(prefix + "password", "")
            host = settings.value(prefix + "host", "Non défini")
            port = settings.value(prefix + "port", "5432")  # Par défaut, port 5432

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
        Teste la connexion à la base de données PostgreSQL sélectionnée et affiche le résultat dans log_message.
        """
        try:
            selected_connection = self.ui.comboBoxConnections.currentText()
            if not selected_connection:
                self.log_message("Erreur : Aucune connexion sélectionnée.")
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
                return

            # Tester la connexion avec psycopg2
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            
            self.log_message(f"Connexion sélectionnée : {selected_connection}")
            self.log_message(f"Base de données : {dbname}")
            self.log_message(f"Utilisateur : {user if user else 'Non défini'}")
            self.log_message(f"Mot de passe : {'Défini' if password else 'Non défini'}")
            self.log_message(f"Hôte : {host}")
            self.log_message(f"Port : {port}")
            
            self.log_message(f"Connexion réussie à la base de données '{dbname}' sur {host}:{port}.")
            conn.close()
        except Exception as e:
            self.log_message(f"Erreur lors de la connexion : {str(e)}")
