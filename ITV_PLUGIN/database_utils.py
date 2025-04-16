import psycopg2
from contextlib import contextmanager
from qgis.core import QgsSettings
from PyQt5.QtWidgets import QMessageBox
from functools import wraps


class DatabaseUtils:
    def __init__(self, ui, log_message):
        self.ui = ui
        self.log_message = log_message

    def handle_errors(func):
        """
        Décorateur pour centraliser la gestion des erreurs.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except psycopg2.OperationalError as e:
                self.log_message(f"Erreur de connexion : {str(e)}")
                QMessageBox.critical(None, "Erreur de connexion", f"Erreur de connexion : {str(e)}")
            except psycopg2.Error as e:
                self.log_message(f"Erreur SQL : {str(e)}")
                QMessageBox.critical(None, "Erreur SQL", f"Erreur SQL : {str(e)}")
            except Exception as e:
                self.log_message(f"Erreur inattendue : {str(e)}")
                QMessageBox.critical(None, "Erreur inattendue", f"Erreur inattendue : {str(e)}")
        return wrapper

    @handle_errors
    def get_connection_params(self, selected_connection):
        """
        Récupère les paramètres de connexion PostgreSQL depuis QgsSettings.
        """
        settings = QgsSettings()
        prefix = f"PostgreSQL/connections/{selected_connection}/"

        return {
            "dbname": settings.value(prefix + "database", ""),
            "user": self.ui.lineEditDatabaseUser.text() or settings.value(prefix + "username", ""),
            "password": self.ui.lineEditDatabasePassword.text() or settings.value(prefix + "password", ""),
            "host": settings.value(prefix + "host", "localhost"),
            "port": settings.value(prefix + "port", "5432"),
        }

    @handle_errors
    def test_database_connection(self, selected_connection):
        """
        Teste la connexion à la base de données PostgreSQL sélectionnée.
        """
        params = self.get_connection_params(selected_connection)
        if not params["dbname"] or not params["user"] or not params["password"]:
            self.log_message("Erreur : Les informations de connexion sont incomplètes.")
            QMessageBox.critical(None, "Erreur", "Les informations de connexion sont incomplètes.")
            return False

        conn = psycopg2.connect(**params)
        conn.close()
        self.log_message(f"Connexion réussie à la base de données '{params['dbname']}' sur {params['host']}:{params['port']}.")
        return True

    @handle_errors
    def execute_query(self, selected_connection, query, values=None):
        """
        Exécute une requête SQL sur la base de données PostgreSQL.
        """
        params = self.get_connection_params(selected_connection)
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
        cursor.close()
        conn.close()
        self.log_message("Requête exécutée avec succès.")

    @handle_errors
    def truncate_table(self, selected_connection, table_name):
        """
        Vide une table PostgreSQL avec CASCADE.
        """
        query = f"TRUNCATE TABLE {table_name} CASCADE;"
        self.execute_query(selected_connection, query)
        self.log_message(f"Table '{table_name}' vidée avec succès.")

    @contextmanager
    @handle_errors
    def connection(self, selected_connection):
        """
        Gestionnaire de contexte pour la connexion à la base de données PostgreSQL.
        """
        params = self.get_connection_params(selected_connection)
        conn = None
        try:
            conn = psycopg2.connect(**params)
            yield conn
        finally:
            if conn:
                conn.close()
