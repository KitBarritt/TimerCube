/* TimerCube translations — EN / FR / DE / ES
 * Encoding: UTF-8
 * One entry per line. Edit the quoted strings only — do not change the key names on the left.
 * Non-breaking space (invisible) is used before : and ? in French — type it with Ctrl+Shift+Space. */

window.TRANSLATIONS = {

  /* ── English ──────────────────────────────────────────────────────────── */
  en: {

    // Navigation
    nav_timer:             'Timer',
    nav_speakers:          'Speakers',
    nav_report:            'Report',
    nav_settings:          'Settings',

    // Timer controls
    btn_start:             'Start',
    btn_running:           'Running…',
    btn_stop:              'Stop',
    btn_reset:             'Reset',

    // Section labels
    label_presets:         'Presets',
    label_speaker:         'Speaker',
    label_manual_light:    'Manual light',

    // Speaker dropdown
    opt_no_speaker:        '— No speaker —',

    // Light buttons
    light_off:             'Off',
    light_green:           'Green',
    light_amber:           'Amber',
    light_red:             'Red',
    light_flash:           'Flash',

    // Status
    st_connecting:         'Connecting…',
    st_connected:          'Connected',
    st_reconnecting:       'Reconnecting…',
    threshold_manual:      'Manual mode',

    // Preset labels
    pre_1min:              '1 Minute',
    pre_table_topics:      'Table Topics',
    pre_evaluations:       'Evaluations',
    pre_icebreaker:        'Icebreaker',
    pre_5_7min:            '5–7 Minutes',
    pre_10min:             '10 Minutes',
    pre_12min:             '12 Minutes',
    pre_15min:             '15 Minutes',
    pre_20min:             '20 Minutes',
    pre_manual:            'Manual',
    pre_none:              '—',

    // Settings — brightness
    h_brightness:          'Display Brightness',
    lbl_brightness:        'Brightness:',

    // Settings — WiFi
    h_wifi:                'WiFi Networks',
    btn_add:               '+ Add',
    btn_save_connect:      'Save & Connect',
    no_networks:           'No networks saved.',
    btn_edit:              'Edit',
    lbl_ssid:              'SSID',
    lbl_password:          'Password',
    lbl_static_ip:         'Static IP',
    lbl_static_ip_hint:    '(optional — leave blank for DHCP)',
    btn_apply:             'Apply',
    btn_cancel:            'Cancel',

    // Settings — hotspot
    h_hotspot:             'Hotspot (fallback AP)',
    hint_open_network:     'Leave password blank for open network.',

    // Settings — connection info
    h_conn_info:           'Connection Info',
    lbl_mode:              'Mode',
    lbl_ip:                'IP address',
    lbl_url:               'URL',
    lbl_ap_ssid:           'AP SSID',

    // Settings — reboot / toasts
    btn_reboot:            'Reboot Device',
    wifi_saved:            'Saved. Reconnecting WiFi…',
    wifi_save_failed:      'Save failed: ',
    toast_saved:           'Settings saved',
    toast_failed:          'Save failed',
    msg_rebooting:         'Rebooting…',
    confirm_reboot:        'Reboot the device?',

    // Settings — WiFi scan
    h_available:           'Available Networks',
    btn_scan:              'Scan',
    btn_scanning:          'Scanning…',
    scan_placeholder:      'Select a network…',
    scan_empty:            'No networks found.',
    btn_add_scanned:       'Add to list',

    // Settings — language
    h_language:            'Language',

    // Speakers page
    btn_add_row:           '+ Add Row',
    btn_save:              'Save',
    btn_clear_actuals:     'Clear Actuals',
    btn_clear_list:        'Clear List',
    col_num:               '#',
    col_name:              'Name',
    col_preset:            'Preset',
    col_green:             'Green',
    col_amber:             'Amber',
    col_red:               'Red',
    col_flash:             'Flash',
    col_actual:            'Actual',
    confirm_clear_all:     'Clear all speakers?',

    // Report page
    h_report:              'Speech Timing Report',
    btn_refresh:           '↻ Refresh',
    btn_print:             'Print',
    col_speaker:           'Speaker',
    col_status:            'Status',
    msg_loading:           'Loading…',
    msg_no_speakers:       'No speakers recorded yet.',
    msg_error:             'Error loading data.',
    badge_not_timed:       'Not timed',
    badge_over:            'Over',
    badge_red:             'Red',
    badge_amber:           'Amber',
    badge_green:           'Green',
    badge_under:           'Under',
  },

  /* ── Français ─────────────────────────────────────────────────────────── */
  fr: {

    // Navigation
    nav_timer:             'Minuterie',
    nav_speakers:          'Orateurs',
    nav_report:            'Rapport',
    nav_settings:          'Paramètres',

    // Timer controls
    btn_start:             'Démarrer',
    btn_running:           'En cours…',
    btn_stop:              'Arrêter',
    btn_reset:             'Réinitialiser',

    // Section labels
    label_presets:         'Préréglages',
    label_speaker:         'Orateur',
    label_manual_light:    'Lumière manuelle',

    // Speaker dropdown
    opt_no_speaker:        '— Aucun orateur —',

    // Light buttons
    light_off:             'Éteint',
    light_green:           'Vert',
    light_amber:           'Ambre',
    light_red:             'Rouge',
    light_flash:           'Flash',

    // Status
    st_connecting:         'Connexion…',
    st_connected:          'Connecté',
    st_reconnecting:       'Reconnexion…',
    threshold_manual:      'Mode manuel',

    // Preset labels
    pre_1min:              '1 Minute',
    pre_table_topics:      'Sujets improvisés',
    pre_evaluations:       'Évaluations',
    pre_icebreaker:        'Brise-glace',
    pre_5_7min:            '5–7 Minutes',
    pre_10min:             '10 Minutes',
    pre_12min:             '12 Minutes',
    pre_15min:             '15 Minutes',
    pre_20min:             '20 Minutes',
    pre_manual:            'Manuel',
    pre_none:              '—',

    // Settings — brightness
    h_brightness:          "Luminosité de l'affichage",
    lbl_brightness:        'Luminosité :',

    // Settings — WiFi
    h_wifi:                'Réseaux WiFi',
    btn_add:               '+ Ajouter',
    btn_save_connect:      'Enregistrer et connecter',
    no_networks:           'Aucun réseau enregistré.',
    btn_edit:              'Modifier',
    lbl_ssid:              'SSID',
    lbl_password:          'Mot de passe',
    lbl_static_ip:         'IP statique',
    lbl_static_ip_hint:    '(optionnel — laisser vide pour DHCP)',
    btn_apply:             'Appliquer',
    btn_cancel:            'Annuler',

    // Settings — hotspot
    h_hotspot:             "Hotspot (point d'accès de secours)",
    hint_open_network:     'Laisser le mot de passe vide pour un réseau ouvert.',

    // Settings — connection info
    h_conn_info:           'Informations de connexion',
    lbl_mode:              'Mode',
    lbl_ip:                'Adresse IP',
    lbl_url:               'URL',
    lbl_ap_ssid:           "SSID du point d'accès",

    // Settings — reboot / toasts
    btn_reboot:            "Redémarrer l'appareil",
    wifi_saved:            'Enregistré. Reconnexion WiFi…',
    wifi_save_failed:      "Échec de l'enregistrement : ",
    toast_saved:           'Paramètres enregistrés',
    toast_failed:          "Échec de l'enregistrement",
    msg_rebooting:         'Redémarrage…',
    confirm_reboot:        "Redémarrer l'appareil ?",

    // Settings — WiFi scan
    h_available:           'Réseaux disponibles',
    btn_scan:              'Scanner',
    btn_scanning:          'Analyse…',
    scan_placeholder:      'Sélectionner un réseau…',
    scan_empty:            'Aucun réseau trouvé.',
    btn_add_scanned:       'Ajouter à la liste',

    // Settings — language
    h_language:            'Langue',

    // Speakers page
    btn_add_row:           '+ Ajouter une ligne',
    btn_save:              'Enregistrer',
    btn_clear_actuals:     'Effacer les temps réels',
    btn_clear_list:        'Effacer la liste',
    col_num:               '#',
    col_name:              'Nom',
    col_preset:            'Préréglage',
    col_green:             'Vert',
    col_amber:             'Ambre',
    col_red:               'Rouge',
    col_flash:             'Flash',
    col_actual:            'Temps réel',
    confirm_clear_all:     'Effacer tous les orateurs ?',

    // Report page
    h_report:              'Rapport de chronométrage',
    btn_refresh:           '↻ Actualiser',
    btn_print:             'Imprimer',
    col_speaker:           'Orateur',
    col_status:            'État',
    msg_loading:           'Chargement…',
    msg_no_speakers:       'Aucun orateur enregistré.',
    msg_error:             'Erreur lors du chargement des données.',
    badge_not_timed:       'Non chronométré',
    badge_over:            'Dépassé',
    badge_red:             'Rouge',
    badge_amber:           'Ambre',
    badge_green:           'Vert',
    badge_under:           'En dessous',
  },

  /* ── Deutsch ──────────────────────────────────────────────────────────── */
  de: {

    // Navigation
    nav_timer:             'Timer',
    nav_speakers:          'Redner',
    nav_report:            'Bericht',
    nav_settings:          'Einstellungen',

    // Timer controls
    btn_start:             'Start',
    btn_running:           'Läuft…',
    btn_stop:              'Stop',
    btn_reset:             'Zurücksetzen',

    // Section labels
    label_presets:         'Voreinstellungen',
    label_speaker:         'Redner',
    label_manual_light:    'Manuelle Lampe',

    // Speaker dropdown
    opt_no_speaker:        '— Kein Redner —',

    // Light buttons
    light_off:             'Aus',
    light_green:           'Grün',
    light_amber:           'Gelb',
    light_red:             'Rot',
    light_flash:           'Blinken',

    // Status
    st_connecting:         'Verbinden…',
    st_connected:          'Verbunden',
    st_reconnecting:       'Erneut verbinden…',
    threshold_manual:      'Manueller Modus',

    // Preset labels
    pre_1min:              '1 Minute',
    pre_table_topics:      'Stegreifrede',
    pre_evaluations:       'Bewertungen',
    pre_icebreaker:        'Eisbrecher',
    pre_5_7min:            '5–7 Minuten',
    pre_10min:             '10 Minuten',
    pre_12min:             '12 Minuten',
    pre_15min:             '15 Minuten',
    pre_20min:             '20 Minuten',
    pre_manual:            'Manuell',
    pre_none:              '—',

    // Settings — brightness
    h_brightness:          'Anzeigehelligkeit',
    lbl_brightness:        'Helligkeit:',

    // Settings — WiFi
    h_wifi:                'WLAN-Netzwerke',
    btn_add:               '+ Hinzufügen',
    btn_save_connect:      'Speichern & Verbinden',
    no_networks:           'Keine Netzwerke gespeichert.',
    btn_edit:              'Bearbeiten',
    lbl_ssid:              'SSID',
    lbl_password:          'Passwort',
    lbl_static_ip:         'Statische IP',
    lbl_static_ip_hint:    '(optional — leer lassen für DHCP)',
    btn_apply:             'Übernehmen',
    btn_cancel:            'Abbrechen',

    // Settings — hotspot
    h_hotspot:             'Hotspot (Reserve-AP)',
    hint_open_network:     'Passwort leer lassen für offenes Netzwerk.',

    // Settings — connection info
    h_conn_info:           'Verbindungsinfo',
    lbl_mode:              'Modus',
    lbl_ip:                'IP-Adresse',
    lbl_url:               'URL',
    lbl_ap_ssid:           'AP-SSID',

    // Settings — reboot / toasts
    btn_reboot:            'Gerät neu starten',
    wifi_saved:            'Gespeichert. WLAN wird neu verbunden…',
    wifi_save_failed:      'Speichern fehlgeschlagen: ',
    toast_saved:           'Einstellungen gespeichert',
    toast_failed:          'Speichern fehlgeschlagen',
    msg_rebooting:         'Neustart…',
    confirm_reboot:        'Gerät neu starten?',

    // Settings — WiFi scan
    h_available:           'Verfügbare Netzwerke',
    btn_scan:              'Scannen',
    btn_scanning:          'Scannen…',
    scan_placeholder:      'Netzwerk auswählen…',
    scan_empty:            'Keine Netzwerke gefunden.',
    btn_add_scanned:       'Zur Liste hinzufügen',

    // Settings — language
    h_language:            'Sprache',

    // Speakers page
    btn_add_row:           '+ Zeile hinzufügen',
    btn_save:              'Speichern',
    btn_clear_actuals:     'Ist-Zeiten löschen',
    btn_clear_list:        'Liste löschen',
    col_num:               '#',
    col_name:              'Name',
    col_preset:            'Voreinstellung',
    col_green:             'Grün',
    col_amber:             'Gelb',
    col_red:               'Rot',
    col_flash:             'Blinken',
    col_actual:            'Ist-Zeit',
    confirm_clear_all:     'Alle Redner löschen?',

    // Report page
    h_report:              'Redezeiten-Bericht',
    btn_refresh:           '↻ Aktualisieren',
    btn_print:             'Drucken',
    col_speaker:           'Redner',
    col_status:            'Status',
    msg_loading:           'Laden…',
    msg_no_speakers:       'Noch keine Redner aufgezeichnet.',
    msg_error:             'Fehler beim Laden der Daten.',
    badge_not_timed:       'Nicht gemessen',
    badge_over:            'Überzogen',
    badge_red:             'Rot',
    badge_amber:           'Gelb',
    badge_green:           'Grün',
    badge_under:           'Unterschritten',
  },

  /* ── Español ──────────────────────────────────────────────────────────── */
  es: {

    // Navigation
    nav_timer:             'Temporizador',
    nav_speakers:          'Oradores',
    nav_report:            'Informe',
    nav_settings:          'Configuración',

    // Timer controls
    btn_start:             'Iniciar',
    btn_running:           'En marcha…',
    btn_stop:              'Detener',
    btn_reset:             'Restablecer',

    // Section labels
    label_presets:         'Ajustes predefinidos',
    label_speaker:         'Orador',
    label_manual_light:    'Luz manual',

    // Speaker dropdown
    opt_no_speaker:        '— Sin orador —',

    // Light buttons
    light_off:             'Apagado',
    light_green:           'Verde',
    light_amber:           'Ámbar',
    light_red:             'Rojo',
    light_flash:           'Destello',

    // Status
    st_connecting:         'Conectando…',
    st_connected:          'Conectado',
    st_reconnecting:       'Reconectando…',
    threshold_manual:      'Modo manual',

    // Preset labels
    pre_1min:              '1 Minuto',
    pre_table_topics:      'Temas de mesa',
    pre_evaluations:       'Evaluaciones',
    pre_icebreaker:        'Rompehielos',
    pre_5_7min:            '5–7 Minutos',
    pre_10min:             '10 Minutos',
    pre_12min:             '12 Minutos',
    pre_15min:             '15 Minutos',
    pre_20min:             '20 Minutos',
    pre_manual:            'Manual',
    pre_none:              '—',

    // Settings — brightness
    h_brightness:          'Brillo de pantalla',
    lbl_brightness:        'Brillo:',

    // Settings — WiFi
    h_wifi:                'Redes WiFi',
    btn_add:               '+ Añadir',
    btn_save_connect:      'Guardar y conectar',
    no_networks:           'No hay redes guardadas.',
    btn_edit:              'Editar',
    lbl_ssid:              'SSID',
    lbl_password:          'Contraseña',
    lbl_static_ip:         'IP estática',
    lbl_static_ip_hint:    '(opcional — dejar en blanco para DHCP)',
    btn_apply:             'Aplicar',
    btn_cancel:            'Cancelar',

    // Settings — hotspot
    h_hotspot:             'Punto de acceso (AP de respaldo)',
    hint_open_network:     'Dejar contraseña en blanco para red abierta.',

    // Settings — connection info
    h_conn_info:           'Información de conexión',
    lbl_mode:              'Modo',
    lbl_ip:                'Dirección IP',
    lbl_url:               'URL',
    lbl_ap_ssid:           'SSID del AP',

    // Settings — reboot / toasts
    btn_reboot:            'Reiniciar dispositivo',
    wifi_saved:            'Guardado. Reconectando WiFi…',
    wifi_save_failed:      'Error al guardar: ',
    toast_saved:           'Configuración guardada',
    toast_failed:          'Error al guardar',
    msg_rebooting:         'Reiniciando…',
    confirm_reboot:        '¿Reiniciar el dispositivo?',

    // Settings — WiFi scan
    h_available:           'Redes disponibles',
    btn_scan:              'Escanear',
    btn_scanning:          'Escaneando…',
    scan_placeholder:      'Seleccionar una red…',
    scan_empty:            'No se encontraron redes.',
    btn_add_scanned:       'Añadir a la lista',

    // Settings — language
    h_language:            'Idioma',

    // Speakers page
    btn_add_row:           '+ Añadir fila',
    btn_save:              'Guardar',
    btn_clear_actuals:     'Borrar tiempos reales',
    btn_clear_list:        'Borrar lista',
    col_num:               '#',
    col_name:              'Nombre',
    col_preset:            'Predefinido',
    col_green:             'Verde',
    col_amber:             'Ámbar',
    col_red:               'Rojo',
    col_flash:             'Destello',
    col_actual:            'Tiempo real',
    confirm_clear_all:     '¿Borrar todos los oradores?',

    // Report page
    h_report:              'Informe de tiempos de discurso',
    btn_refresh:           '↻ Actualizar',
    btn_print:             'Imprimir',
    col_speaker:           'Orador',
    col_status:            'Estado',
    msg_loading:           'Cargando…',
    msg_no_speakers:       'Aún no hay oradores registrados.',
    msg_error:             'Error al cargar los datos.',
    badge_not_timed:       'Sin cronometrar',
    badge_over:            'Excedido',
    badge_red:             'Rojo',
    badge_amber:           'Ámbar',
    badge_green:           'Verde',
    badge_under:           'Por debajo',
  }

};
