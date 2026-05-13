from __future__ import annotations

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # Menus
        "menu_file": "&File",
        "menu_new": "&New Session",
        "menu_open": "&Open…",
        "menu_save": "&Save",
        "menu_save_as": "Save &As…",
        "menu_settings": "&Settings",
        "menu_language": "Language",
        "lang_en": "English",
        "lang_es": "Español",
        "lang_gl": "Galego",
        # Toolbar
        "toolbar_stop_all": "Stop All",
        # Table headers
        "col_name": "Name",
        "col_duration": "Duration",
        "col_play": "Play",
        "col_loop": "Loop",
        "col_volume": "Volume",
        # Dialogs
        "dlg_new_title": "New Session",
        "dlg_new_body": "Clear the current session?",
        "dlg_open_title": "Open Session",
        "dlg_open_filter": "TuxCue Sessions (*.tuxcue.json)",
        "dlg_save_title": "Save Session",
        "dlg_missing_title": "Missing Files",
        "dlg_error_title": "Playback Error",
        "dlg_lang_title": "Language",
        "dlg_lang_body": "Changes will take effect after restarting TuxCue.",
        # Filter bar
        "filter_search_placeholder": "Search tracks…",
        "filter_duration_label": "Duration:",
        "filter_all": "All",
        "filter_under_30s": "< 30s",
        "filter_30s_2m": "30s – 2m",
        "filter_2m_5m": "2m – 5m",
        "filter_over_5m": "> 5m",
        # Tooltips
        "tooltip_missing": "File not found: {path}",
    },
    "es": {
        # Menus
        "menu_file": "&Archivo",
        "menu_new": "&Nueva sesión",
        "menu_open": "&Abrir…",
        "menu_save": "&Guardar",
        "menu_save_as": "Guardar &como…",
        "menu_settings": "&Configuración",
        "menu_language": "Idioma",
        "lang_en": "English",
        "lang_es": "Español",
        "lang_gl": "Galego",
        # Toolbar
        "toolbar_stop_all": "Parar todo",
        # Table headers
        "col_name": "Nombre",
        "col_duration": "Duración",
        "col_play": "Play",
        "col_loop": "Loop",
        "col_volume": "Volumen",
        # Dialogs
        "dlg_new_title": "Nueva sesión",
        "dlg_new_body": "¿Limpiar la sesión actual?",
        "dlg_open_title": "Abrir sesión",
        "dlg_open_filter": "Sesiones TuxCue (*.tuxcue.json)",
        "dlg_save_title": "Guardar sesión",
        "dlg_missing_title": "Ficheros no encontrados",
        "dlg_error_title": "Error de reproducción",
        "dlg_lang_title": "Idioma",
        "dlg_lang_body": "Los cambios se aplicarán al reiniciar TuxCue.",
        # Filter bar
        "filter_search_placeholder": "Buscar pistas…",
        "filter_duration_label": "Duración:",
        "filter_all": "Todas",
        "filter_under_30s": "< 30s",
        "filter_30s_2m": "30s – 2m",
        "filter_2m_5m": "2m – 5m",
        "filter_over_5m": "> 5m",
        # Tooltips
        "tooltip_missing": "Fichero no encontrado: {path}",
    },
    "gl": {
        # Menus
        "menu_file": "&Arquivo",
        "menu_new": "&Nova sesión",
        "menu_open": "&Abrir…",
        "menu_save": "&Gardar",
        "menu_save_as": "Gardar &como…",
        "menu_settings": "&Configuración",
        "menu_language": "Idioma",
        "lang_en": "English",
        "lang_es": "Español",
        "lang_gl": "Galego",
        # Toolbar
        "toolbar_stop_all": "Parar todo",
        # Table headers
        "col_name": "Nome",
        "col_duration": "Duración",
        "col_play": "Play",
        "col_loop": "Loop",
        "col_volume": "Volume",
        # Dialogs
        "dlg_new_title": "Nova sesión",
        "dlg_new_body": "¿Limpar a sesión actual?",
        "dlg_open_title": "Abrir sesión",
        "dlg_open_filter": "Sesións TuxCue (*.tuxcue.json)",
        "dlg_save_title": "Gardar sesión",
        "dlg_missing_title": "Ficheiros non atopados",
        "dlg_error_title": "Erro de reproduçón",
        "dlg_lang_title": "Idioma",
        "dlg_lang_body": "Os cambios aplicaránse ao reiniciar TuxCue.",
        # Filter bar
        "filter_search_placeholder": "Buscar pistas…",
        "filter_duration_label": "Duración:",
        "filter_all": "Todas",
        "filter_under_30s": "< 30s",
        "filter_30s_2m": "30s – 2m",
        "filter_2m_5m": "2m – 5m",
        "filter_over_5m": "> 5m",
        # Tooltips
        "tooltip_missing": "Ficheiro non atopado: {path}",
    },
}

SUPPORTED_LOCALES: list[str] = list(STRINGS.keys())
