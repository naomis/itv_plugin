# ITV Plugin

[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)

## Description

ITV Plugin is a QGIS plugin designed to inspect ITV (Inspection Technique des Voies) data, display results in QGIS, and manage associated data. It provides tools for importing, processing, and visualizing ITV data, ensuring seamless integration with PostgreSQL databases and geometric layers in QGIS.

The plugin supports:
- Displaying ITV data in QGIS (SQL views and PostgreSQL tables)
- Importing data from TXT and CSV files
- Updating PostgreSQL tables with mappings
- Managing PostgreSQL connections
- Exporting messages and logs to CSV
- Progress tracking for processing steps

## Features

- **Data Visualization**: Display ITV data in geometric layers and SQL views.
- **Data Import**: Import data from TXT and CSV files.
- **Database Management**: Update PostgreSQL tables with mappings and manage connections.
- **Export Tools**: Export messages and logs in CSV format.
- **Progress Tracking**: Follow processing steps with a progress bar.
- **Compatibility**: Fully compatible with QGIS 3.x.

## Installation

1. Download the plugin from the [repository](https://github.com/naomis/itv-plugin).
2. Open QGIS and navigate to `Plugins > Manage and Install Plugins`.
3. Click on `Install from ZIP` and select the downloaded plugin file.
4. Activate the plugin from the `Installed` tab.

## Usage

1. Open QGIS and activate the ITV Plugin.
2. Use the toolbar or menu options to:
   - Import ITV data from TXT or CSV files.
   - Visualize ITV data in geometric layers or SQL views.
   - Update PostgreSQL tables with mappings.
   - Export logs or messages to CSV.
3. Configure PostgreSQL connections as needed for seamless data management.

## Source Code

The source code is available on GitHub: [https://github.com/naomis/itv-plugin](https://github.com/naomis/itv-plugin).  
Report issues or feature requests via the [issue tracker](https://github.com/naomis/itv-plugin/issues).

## About

The ITV Plugin was developed by **Gabriel Noiret** at **NAOMIS**.  
For inquiries, contact: [g.noiret@naomis.fr](mailto:g.noiret@naomis.fr)  
Visit our website: [https://www.naomis.fr](https://www.naomis.fr)

## License

This plugin is licensed under the GNU General Public License v3.0. See the [LICENSE](https://www.gnu.org/licenses/gpl-3.0.html) file for details.
