import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date, time, timedelta
import itertools
import re

# --- ASSETS ---
ACOEM_LOGO_NEW = "https://cdn.bfldr.com/Q3Z2TZY7/at/b4z3s28jpswp92h6z35h9f3/ACOEM-LOGO-WithoutBaseline-RGB-Bicolor.jpg?auto=webp&format=jpg"
ACOEM_COLORS = ['#ff6952', '#2c5078', '#96c8de', '#FFB000', '#50C878', '#808080', '#000000']

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Cadence Data", page_icon=ACOEM_LOGO_NEW, layout="wide")

st.markdown("""
    <style>
        .block-container { padding-top: 2rem; padding-bottom: 1rem; }
        .logo-container { background-color: white; padding: 12px; border-radius: 6px; display: flex; justify-content: center; align-items: center; margin-bottom: 20px; }
        .streamlit-expanderHeader { font-size: 1rem; font-weight: bold; color: #ff6952; }
        .project-detected { color: #50C878; font-size: 0.85rem; font-weight: bold; margin-top: -10px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'df_1h' not in st.session_state: st.session_state['df_1h'] = None
if 'df_15m' not in st.session_state: st.session_state['df_15m'] = None
if 'df_aq' not in st.session_state: st.session_state['df_aq'] = None
if 'df_alerts' not in st.session_state: st.session_state['df_alerts'] = None
if 'has_run' not in st.session_state: st.session_state['has_run'] = False

# --- TRANSLATIONS ---
translations = {
    "Français": {
        "auth_title": " 1. Authentification", "api_key": "Clé API", "api_help": "Commence par EZfX...",
        "target_title": " 2. Cible", "proj_id": "ID du Projet", "dash_id": "ID du Dashboard (Alertes)",
        "points": "IDs des Points", "points_help": "Ex: 1797, 1798",
        "settings_title": " 3. Paramètres", "metrics": "Sélection des Métriques :",
        "hourly": "Par Heure (1h)", "short": "Court (15min)", "time_range": "Période :",
        "limit_db": "Ligne de limite (dB) (0 = désactivé):",
        "start": "Début", "end": "Fin", "btn_load": " CHARGER LES DONNÉES", "dashboard_title": "Tableau de Bord",
        "tab_1h": " Données (1h)", "tab_15m": " Données (15min)", "tab_aq": " Données AQ", "tab_alerts": " Alertes",
        "no_data": "Aucune donnée trouvée pour ces filtres.", "data_table": "Tableau de Données",
        "rows": "lignes", "export": " Exporter en CSV", "missing_key": " Clé API manquante",
        "invalid_points": " Format des IDs de points invalide", "analyzing": " Analyse de {} points...",
        "fetching": "Récupération des données...", "no_alerts": "Aucune alerte trouvée pour cette période (Vérifiez le Dashboard ID).",
        "unknown": "Inconnu", "status_summary": "###  Résumé des statuts", "total_alerts": "Total des alertes",
        "val_alerts": " Validées", "unval_alerts": " Non Validées", "open_alerts": " Ouvertes (à traiter)",
        "chart_title_1": "#### Nombre d'alertes par Point et Type", "chart_title_2": "#### Sources Identifiées (IA)",
        "no_ident": "Aucune alerte identifiée.", "no_source_info": "Aucune information de source.",
        "raw_data": "###  Données Brutes", "api_empty": "L'API n'a renvoyé aucune donnée. Vérifiez les dates ou les IDs."
    },
    "Español": {
        "auth_title": " 1. Autenticación", "api_key": "Clave API", "api_help": "Empieza con EZfX...",
        "target_title": " 2. Objetivo", "proj_id": "ID del Proyecto", "dash_id": "ID del Dashboard (Alertas)",
        "points": "IDs de los Puntos", "points_help": "Ej: 1797, 1798",
        "settings_title": " 3. Configuración", "metrics": "Selección de Métricas:",
        "hourly": "Por Hora (1h)", "short": "Corto (15min)", "time_range": "Rango de Tiempo:",
        "limit_db": "Línea de límite (dB) (0 = desactivado):",
        "start": "Inicio", "end": "Fin", "btn_load": " CARGAR DATOS", "dashboard_title": "Dashboard de Datos",
        "tab_1h": " Datos (1h)", "tab_15m": " Datos (15min)", "tab_aq": " Datos AQ", "tab_alerts": " Alertas",
        "no_data": "No se encontraron datos para los filtros seleccionados.", "data_table": "Tabla de Datos",
        "rows": "filas", "export": " Exportar CSV", "missing_key": " Falta la Clave API",
        "invalid_points": " Formato de IDs de Puntos inválido", "analyzing": " Analizando {} puntos...",
        "fetching": "Obteniendo datos de la API...", "no_alerts": "No se encontraron alertas (Compruebe el Dashboard ID).",
        "unknown": "Desconocido", "status_summary": "###  Resumen de estados", "total_alerts": "Total de alertas",
        "val_alerts": " Validadas", "unval_alerts": " No Validadas", "open_alerts": " Abiertas (a tratar)",
        "chart_title_1": "#### Número de alertas por Punto y Tipo", "chart_title_2": "#### Fuentes Identificadas (IA)",
        "no_ident": "Ninguna alerta identificada.", "no_source_info": "Sin información de fuente.",
        "raw_data": "###  Resumen de datos", "api_empty": "La API no devolvió datos. Comprueba las fechas o los IDs."
    },
    "Català": {
        "auth_title": " 1. Autenticació", "api_key": "Clau API", "api_help": "Comença amb EZfX...",
        "target_title": " 2. Objectiu", "proj_id": "ID del Projecte", "dash_id": "ID del Dashboard (Alertes)",
        "points": "IDs dels Punts", "points_help": "Ex: 1797, 1798",
        "settings_title": " 3. Configuració", "metrics": "Selecció de Mètriques:",
        "hourly": "Per Hora (1h)", "short": "Curt (15min)", "time_range": "Rang de Temps:",
        "limit_db": "Línia de límit (dB) (0 = desactivat):",
        "start": "Inici", "end": "Fi", "btn_load": " CARREGAR DADES", "dashboard_title": "Dashboard de Dades",
        "tab_1h": " Dades (1h)", "tab_15m": " Dades (15min)", "tab_aq": " Dades AQ", "tab_alerts": " Alertes",
        "no_data": "No s'han trobat dades per als filtres seleccionats.", "data_table": "Taula de Dades",
        "rows": "files", "export": " Exportar CSV", "missing_key": " Falta la Clau API",
        "invalid_points": " Format d'IDs de Punts invàlid", "analyzing": " Analitzant {} punts...",
        "fetching": "Obtenint dades de l'API...", "no_alerts": "No s'han trobat alertes (Comproveu el Dashboard ID).",
        "unknown": "Desconegut", "status_summary": "###  Resum d'estats", "total_alerts": "Total d'alertes",
        "val_alerts": " Validades", "unval_alerts": " No Validades", "open_alerts": " Obertes (a tractar)",
        "chart_title_1": "#### Nombre d'alertes per Punt i Tipus", "chart_title_2": "#### Fonts Identificades (IA)",
        "no_ident": "Cap alerta identificada.", "no_source_info": "Sense informació de font.",
        "raw_data": "###  Dades Brutes", "api_empty": "L'API no ha retornat dades. Comprova les dates o els IDs."
    },
    "Deutsch": {
        "auth_title": " 1. Authentifizierung", "api_key": "API-Schlüssel", "api_help": "Beginnt mit EZfX...",
        "target_title": " 2. Ziel", "proj_id": "Projekt-ID", "dash_id": "Dashboard-ID (Alarme)",
        "points": "Messpunkt-IDs", "points_help": "Z.B.: 1797, 1798",
        "settings_title": " 3. Einstellungen", "metrics": "Metriken auswählen:",
        "hourly": "Stündlich (1h)", "short": "Kurzzeit (15min)", "time_range": "Zeitraum:",
        "limit_db": "Grenzlinie (dB) (0 = deaktiviert):",
        "start": "Start", "end": "Ende", "btn_load": " DATEN LADEN", "dashboard_title": "Dashboard",
        "tab_1h": " Daten (1h)", "tab_15m": " Daten (15min)", "tab_aq": " AQ-Daten", "tab_alerts": " Alarme",
        "no_data": "Keine Daten für diese Filter gefunden.", "data_table": "Datentabelle",
        "rows": "Zeilen", "export": " Als CSV export
