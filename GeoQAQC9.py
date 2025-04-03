import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from io import StringIO, BytesIO
import base64
import re
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import tempfile
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns

# Configuration de la page
st.set_page_config(
    page_title="GeoQAQC",
    page_icon="🔍",
    layout="wide"
)

# ----------------------------------------
# REMPLACEMENT COMPLET DE LA GESTION DES ONGLETS
# ----------------------------------------

# Utiliser un état de session pour suivre l'onglet actif
if 'tab' not in st.session_state:
    st.session_state.tab = "Type de Contrôle"  # Onglet par défaut

# Fonction pour créer un identifiant valide à partir d'un nom de colonne
def make_valid_id(column_name):
    # Remplacer les caractères non alphanumériques par des underscores
    return re.sub(r'\W+', '_', column_name).lower()

# Fonction pour mapper les colonnes
def map_columns(df, mapping_dict):
    # Créer un nouveau DataFrame avec les colonnes mappées
    mapped_df = pd.DataFrame()
    
    for target_col, source_col in mapping_dict.items():
        if source_col in df.columns:
            mapped_df[target_col] = df[source_col]
    
    return mapped_df

# Fonction pour générer un logo géologique
def generate_geology_logo():
    # Créer une figure matplotlib
    fig, ax = plt.subplots(figsize=(2, 2), dpi=150)
    
    # Définir un fond beige clair
    ax.set_facecolor('#f5f2e9')
    
    # Créer un cercle qui représente une coupe géologique
    circle = plt.Circle((0.5, 0.5), 0.4, fill=False, edgecolor='#8c6d46', linewidth=2.5)
    ax.add_patch(circle)
    
    # Ajouter quelques lignes de stratification
    for i in range(5):
        y = 0.3 + i * 0.08
        ax.plot([0.1, 0.9], [y, y], color='#8c6d46', linewidth=1.5, linestyle='-')
    
    # Ajouter un symbole représentant un cristal/minéral
    crystal_x = [0.5, 0.6, 0.5, 0.4, 0.5]
    crystal_y = [0.7, 0.5, 0.3, 0.5, 0.7]
    ax.fill(crystal_x, crystal_y, color='#3a7359', alpha=0.8)
    
    # Ajouter des points représentant des minéraux
    for i in range(8):
        x = 0.2 + 0.6 * np.random.random()
        y = 0.2 + 0.6 * np.random.random()
        size = 20 + 30 * np.random.random()
        ax.scatter(x, y, color='#b5651d', s=size, alpha=0.7, zorder=3)
    
    # Supprimer les axes
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Convertir la figure en image
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    plt.close(fig)
    buf.seek(0)
    
    return buf

# Fonction pour exporter un graphique Plotly en PNG
def export_plotly_to_png(fig):
    img_bytes = fig.to_image(format="png", width=1200, height=800, scale=2)
    return img_bytes

# Fonction pour exporter un DataFrame en PDF
def export_to_pdf(title, fig, stats_dict, results_df, author="Didier Ouedraogo, P.Geo"):
    # Créer un fichier temporaire pour le PDF
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        temp_filename = tmp.name
    
    # Créer un document PDF
    doc = SimpleDocTemplate(temp_filename, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Créer des styles personnalisés
    title_style = ParagraphStyle(
        'TitleStyle', 
        parent=styles['Heading1'], 
        fontSize=16, 
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle', 
        parent=styles['Heading2'], 
        fontSize=14, 
        spaceAfter=10
    )
    normal_style = styles['Normal']
    
    # Liste d'éléments à ajouter au PDF
    elements = []
    
    # Générer le logo
    logo_buffer = generate_geology_logo()
    logo_temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    logo_temp.write(logo_buffer.getvalue())
    logo_temp.close()
    
    # Créer une table pour l'en-tête avec logo
    logo_img = Image(logo_temp.name, width=0.8*inch, height=0.8*inch)
    header_data = [[logo_img, Paragraph(f"<b>GeoQAQC - {title}</b>", title_style)]]
    header_table = Table(header_data, colWidths=[1*inch, 5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (0, 0), (0, 0), 10),
    ]))
    elements.append(header_table)
    
    # Ajouter la date et l'auteur
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}", normal_style))
    elements.append(Paragraph(f"Auteur: {author}", normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Exporter le graphique en PNG
    img_bytes = export_plotly_to_png(fig)
    
    # Sauvegarder l'image temporairement
    img_temp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img_temp.write(img_bytes)
    img_temp.close()
    
    # Ajouter l'image au PDF
    elements.append(Image(img_temp.name, width=6*inch, height=4*inch))
    elements.append(Spacer(1, 0.2*inch))
    
    # Ajouter les statistiques
    elements.append(Paragraph("Statistiques", subtitle_style))
    stats_data = [[k, str(v)] for k, v in stats_dict.items()]
    stats_table = Table(stats_data, colWidths=[3*inch, 3*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Ajouter les résultats
    elements.append(Paragraph("Résultats détaillés", subtitle_style))
    
    # Préparer les données du tableau
    table_data = [results_df.columns.tolist()]
    for i, row in results_df.iterrows():
        table_data.append([str(cell) if not pd.isna(cell) else "" for cell in row.values])
    
    # Créer le tableau
    results_table = Table(table_data, colWidths=None)
    
    # Style du tableau
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('PADDING', (0, 0), (-1, -1), 4),
    ])
    
    # Ajouter le style pour les valeurs hors limites
    if 'Statut' in results_df.columns:
        for i, row in enumerate(table_data[1:], 1):
            status_index = results_df.columns.get_loc('Statut')
            if status_index < len(row) and (row[status_index] == 'Hors limites' or row[status_index] == 'Élevé'):
                style.add('BACKGROUND', (0, i), (-1, i), colors.lightpink)
    
    results_table.setStyle(style)
    elements.append(results_table)
    
    # Ajouter un pied de page
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"GeoQAQC © 2025 - Rapport généré automatiquement", styles['Italic']))
    
    # Créer le document PDF
    doc.build(elements)
    
    # Supprimer les fichiers temporaires
    os.unlink(img_temp.name)
    os.unlink(logo_temp.name)
    
    # Lire le fichier PDF et le retourner comme bytes
    with open(temp_filename, "rb") as f:
        pdf_bytes = f.read()
    
    # Supprimer le fichier PDF temporaire
    os.unlink(temp_filename)
    
    return pdf_bytes

# Définition des données d'exemple
def get_crm_example_data():
    data = """Échantillon,Au_ppm,Cu_pct,Ag_ppm
CRM-001,1.24,0.51,12.5
CRM-002,1.18,0.48,11.9
CRM-003,1.31,0.53,13.2
CRM-004,1.22,0.49,12.1
CRM-005,1.19,0.50,12.4
CRM-006,1.35,0.54,12.8
CRM-007,1.26,0.52,12.3
CRM-008,1.20,0.49,11.8
CRM-009,1.28,0.51,12.6
CRM-010,1.17,0.47,11.7"""
    return data

def get_blank_example_data():
    data = """Sample_ID,Gold_ppb,Copper_ppm,Silver_ppm
BLK-001,1.2,0.8,0.12
BLK-002,0.9,0.6,0.09
BLK-003,1.5,1.1,0.18
BLK-004,0.8,0.5,0.10
BLK-005,1.3,0.9,0.15
BLK-006,1.1,0.7,0.13
BLK-007,1.4,1.0,0.17
BLK-008,0.7,0.4,0.08
BLK-009,1.6,1.2,0.19
BLK-010,1.0,0.6,0.11"""
    return data

def get_duplicate_example_data():
    data = """Original_Sample,Duplicate_Sample,Au_Original,Au_Duplicate,Cu_Original,Cu_Duplicate
S-100,DUP-100,2.45,2.38,0.82,0.79
S-101,DUP-101,3.18,3.26,1.05,1.09
S-102,DUP-102,1.76,1.70,0.58,0.55
S-103,DUP-103,4.21,4.35,1.38,1.42
S-104,DUP-104,2.93,2.85,0.96,0.93
S-105,DUP-105,3.57,3.68,1.17,1.20
S-106,DUP-106,1.98,1.92,0.65,0.63
S-107,DUP-107,3.82,3.75,1.26,1.22
S-108,DUP-108,2.14,2.20,0.70,0.72
S-109,DUP-109,2.67,2.60,0.88,0.85"""
    return data

# Fonction pour calculer les limites pour les CRM
def calculate_crm_limits(reference_value, tolerance_type, tolerance_value, reference_stddev=None):
    if tolerance_type == "Pourcentage (%)":
        tolerance = tolerance_value / 100
        upper_limit = reference_value * (1 + tolerance)
        lower_limit = reference_value * (1 - tolerance)
    else:  # Multiple de l'écart-type
        if reference_stddev is None or reference_stddev == 0:
            st.error("L'écart-type de référence doit être défini et supérieur à zéro pour utiliser ce type de tolérance.")
            return None, None
        upper_limit = reference_value + (tolerance_value * reference_stddev)
        lower_limit = reference_value - (tolerance_value * reference_stddev)
    
    return lower_limit, upper_limit

# Auteur et informations - Sidebar
with st.sidebar:
    # Générer le logo et l'afficher
    logo_bytes = generate_geology_logo()
    st.image(logo_bytes, width=150)
    
    st.markdown("### GeoQAQC")
    st.markdown("*Contrôle Qualité des Analyses Chimiques des Roches*")
    st.markdown("---")
    st.markdown("**Auteur:** Didier Ouedraogo, P.Geo")
    st.markdown("**Version:** 1.0.0")
    
    # Navigation avec boutons radio au lieu d'onglets
    st.markdown("### Navigation")
    tab_selection = st.radio(
        "Sélectionnez une étape:",
        ["Type de Contrôle", "Importation des Données", "Mappage des Colonnes", "Analyse", "Export"],
        index=["Type de Contrôle", "Importation des Données", "Mappage des Colonnes", "Analyse", "Export"].index(st.session_state.tab)
    )
    
    # Mettre à jour la session state si l'utilisateur change l'onglet
    if tab_selection != st.session_state.tab:
        st.session_state.tab = tab_selection
        st.rerun()
    
    # Section d'aide
    with st.expander("Guide d'utilisation"):
        st.markdown("""
        **Comment utiliser cette application:**
        
        1. **Type de Contrôle**: Sélectionnez d'abord le type d'analyse que vous souhaitez effectuer.
        2. **Importation des Données**: Téléchargez ou collez vos données.
        3. **Mappage des Colonnes**: Associez les colonnes de vos données aux champs requis.
        4. **Analyse**: Générez et visualisez les résultats.
        5. **Export**: Exportez les graphiques et rapports en PNG ou PDF.
        
        Des données d'exemple sont disponibles pour chaque type d'analyse afin de vous aider à démarrer rapidement.
        
        Pour toute question, contactez l'auteur.
        """)

# Titre principal
st.title("GeoQAQC")
st.markdown("### Contrôle Qualité des Analyses Chimiques des Roches")
st.markdown(f"**Étape actuelle:** {st.session_state.tab}")
st.markdown("---")

# Initialisation des états de session
if 'data' not in st.session_state:
    st.session_state.data = None
if 'column_mapping' not in st.session_state:
    st.session_state.column_mapping = {}
if 'mapped_data' not in st.session_state:
    st.session_state.mapped_data = None
if 'mapping_done' not in st.session_state:
    st.session_state.mapping_done = False
if 'graph_title' not in st.session_state:
    st.session_state.graph_title = ""
if 'report_author' not in st.session_state:
    st.session_state.report_author = "Didier Ouedraogo, P.Geo"
if 'temp_values' not in st.session_state:
    st.session_state.temp_values = {}
if 'current_fig' not in st.session_state:
    st.session_state.current_fig = None
if 'current_stats' not in st.session_state:
    st.session_state.current_stats = {}
if 'current_results' not in st.session_state:
    st.session_state.current_results = None

# ===== CONTENU SELON L'ONGLET SÉLECTIONNÉ =====
if st.session_state.tab == "Type de Contrôle":
    # ONGLET 1: TYPE DE CONTRÔLE
    st.header("Choisir le Type de Carte de Contrôle")
    
    control_type = st.selectbox(
        "Type de contrôle:",
        ["Standards CRM", "Blancs", "Duplicatas (nuage de points et régression)"],
        key="control_type"
    )
    
    # Sous-onglets pour chaque type de contrôle
    control_subtabs = st.tabs(["Paramètres", "Exemple de données"])
    
    with control_subtabs[0]:
        if control_type == "Standards CRM":
            col1, col2 = st.columns(2)
            
            with col1:
                # Utiliser les valeurs temporaires si disponibles
                default_ref_value = 0.0
                default_ref_stddev = 0.0
                
                if 'temp_values' in st.session_state and 'ref_value' in st.session_state.temp_values:
                    default_ref_value = st.session_state.temp_values.get('ref_value', 0.0)
                    default_ref_stddev = st.session_state.temp_values.get('ref_stddev', 0.0)
                    # Nettoyer après utilisation
                    if 'ref_value' in st.session_state.temp_values:
                        del st.session_state.temp_values['ref_value']
                    if 'ref_stddev' in st.session_state.temp_values:
                        del st.session_state.temp_values['ref_stddev']
                
                reference_value = st.number_input(
                    "Valeur de référence:",
                    min_value=0.0,
                    step=0.0001,
                    format="%.4f",
                    value=default_ref_value,
                    key="reference_value"
                )
                
                reference_stddev = st.number_input(
                    "Écart-type de référence:",
                    min_value=0.0,
                    step=0.0001,
                    format="%.4f",
                    value=default_ref_stddev,
                    key="reference_stddev"
                )
            
            with col2:
                tolerance_type = st.radio(
                    "Type de tolérance:",
                    ["Pourcentage (%)", "Multiple de l'écart-type"],
                    key="tolerance_type"
                )
                
                if tolerance_type == "Pourcentage (%)":
                    default_tolerance = 10.0
                    if 'temp_values' in st.session_state and 'tolerance_percent' in st.session_state.temp_values:
                        default_tolerance = st.session_state.temp_values.get('tolerance_percent', 10.0)
                        # Nettoyer après utilisation
                        del st.session_state.temp_values['tolerance_percent']
                    
                    tolerance_value = st.number_input(
                        "Tolérance (%):",
                        min_value=0.0,
                        max_value=100.0,
                        value=default_tolerance,
                        step=0.1,
                        key="tolerance_percent"
                    )
                else:
                    tolerance_value = st.number_input(
                        "Multiple de l'écart-type:",
                        min_value=0.0,
                        value=2.0,
                        step=0.1,
                        key="tolerance_stddev"
                    )
            
            # Définir les champs requis pour l'analyse
            st.session_state.required_fields = {
                "sample_id": "Identifiant de l'échantillon",
                "measured_value": "Valeur mesurée"
            }
        
        elif control_type == "Blancs":
            # Définir les champs requis pour l'analyse des blancs
            st.session_state.required_fields = {
                "sample_id": "Identifiant du blanc",
                "measured_value": "Valeur mesurée"
            }
        
        elif control_type == "Duplicatas (nuage de points et régression)":
            # Définir les champs requis pour l'analyse des duplicatas
            st.session_state.required_fields = {
                "original_value": "Valeur originale",
                "duplicate_value": "Valeur dupliquée"
            }
        
        # Options de titre et auteur
        st.subheader("Personnalisation du rapport")
        
        st.session_state.graph_title = st.text_input(
            "Titre du graphique et du rapport:",
            value=f"Contrôle Qualité - {control_type}",
            key="graph_title_input"
        )
        
        st.session_state.report_author = st.text_input(
            "Auteur du rapport:",
            value="Didier Ouedraogo, P.Geo",
            key="report_author_input"
        )
    
    with control_subtabs[1]:
        st.subheader(f"Exemple de données pour {control_type}")
        
        if control_type == "Standards CRM":
            example_data = get_crm_example_data()
            st.markdown("""
            ### Format attendu pour l'analyse des Standards CRM
            
            Pour l'analyse des standards CRM, vous avez besoin d'au moins deux colonnes:
            - Une colonne d'**identifiants** pour les échantillons CRM
            - Une colonne de **valeurs mesurées** pour l'élément analysé
            
            Vous mappez ensuite ces colonnes dans l'onglet "Mappage des Colonnes".
            
            #### Exemple:
            """)
            st.code(example_data, language="text")
            
            st.markdown("""
            #### Valeurs recommandées pour le test:
            - **Valeur de référence:** 1.25 (pour Au_ppm)
            - **Écart-type de référence:** 0.05
            - **Tolérance:** 10% ou 2 × écart-type
            """)
            
            if st.button("Utiliser ces données d'exemple", key="use_crm_example"):
                st.session_state.data = pd.read_csv(StringIO(example_data))
                # Stocker temporairement les valeurs recommandées
                st.session_state.temp_values = {
                    'ref_value': 1.25,
                    'ref_stddev': 0.05,
                    'tolerance_percent': 10.0
                }
                st.session_state.tab = "Mappage des Colonnes"
                st.rerun()
                
        elif control_type == "Blancs":
            example_data = get_blank_example_data()
            st.markdown("""
            ### Format attendu pour l'analyse des Blancs
            
            Pour l'analyse des blancs, vous avez besoin d'au moins deux colonnes:
            - Une colonne d'**identifiants** pour les échantillons blancs
            - Une colonne de **valeurs mesurées** pour l'élément analysé
            
            L'application calculera automatiquement la limite de détection (LOD) basée sur ces valeurs.
            
            #### Exemple:
            """)
            st.code(example_data, language="text")
            
            if st.button("Utiliser ces données d'exemple", key="use_blank_example"):
                st.session_state.data = pd.read_csv(StringIO(example_data))
                st.session_state.tab = "Mappage des Colonnes"
                st.rerun()
                
        elif control_type == "Duplicatas (nuage de points et régression)":
            example_data = get_duplicate_example_data()
            st.markdown("""
            ### Format attendu pour l'analyse des Duplicatas
            
            Pour l'analyse des duplicatas, vous avez besoin d'au moins deux colonnes:
            - Une colonne de **valeurs originales** des échantillons
            - Une colonne de **valeurs dupliquées** correspondantes
            
            L'application calculera la régression linéaire, le coefficient de corrélation, et les différences entre les paires.
            
            #### Exemple:
            """)
            st.code(example_data, language="text")
            
            st.markdown("""
            **Note:** Pour les duplicatas, vous devez choisir un élément à analyser (Au, Cu, etc.) et mapper 
            ses colonnes correspondantes (originale et dupliquée) dans l'onglet de mappage.
            """)
            
            if st.button("Utiliser ces données d'exemple", key="use_duplicate_example"):
                st.session_state.data = pd.read_csv(StringIO(example_data))
                st.session_state.tab = "Mappage des Colonnes"
                st.rerun()
    
    # Bouton pour passer à l'onglet suivant
    if st.button("Continuer vers l'importation des données", key="continue_to_import"):
        st.session_state.tab = "Importation des Données"
        st.rerun()

elif st.session_state.tab == "Importation des Données":
    # ONGLET 2: IMPORTATION DES DONNÉES
    st.header("Importer les Données")
    
    import_method = st.radio(
        "Méthode d'importation:",
        ["Téléchargement de fichier", "Copier-coller des données", "Utiliser les données d'exemple"],
        key="import_method"
    )
    
    st.session_state.mapping_done = False  # Réinitialiser l'état de mappage
    
    if import_method == "Téléchargement de fichier":
        uploaded_file = st.file_uploader("Choisir un fichier CSV ou Excel", type=["csv", "txt", "xlsx", "xls"])
        
        if uploaded_file is not None:
            file_extension = uploaded_file.name.split(".")[-1].lower()
            
            try:
                if file_extension in ["xlsx", "xls"]:
                    df = pd.read_excel(uploaded_file)
                else:
                    separator = st.selectbox(
                        "Séparateur:",
                        [",", ";", "Tab"],
                        key="file_separator"
                    )
                    
                    sep_dict = {",": ",", ";": ";", "Tab": "\t"}
                    if separator == "Tab":
                        df = pd.read_csv(uploaded_file, sep="\t")
                    else:
                        df = pd.read_csv(uploaded_file, sep=separator)
                
                st.session_state.data = df
                st.success(f"Fichier chargé avec succès! {len(df)} lignes et {len(df.columns)} colonnes.")
                st.write("Aperçu des données:")
                st.dataframe(df.head())
                
                # Bouton pour continuer
                if st.button("Continuer vers le mappage des colonnes", key="continue_to_mapping_file"):
                    st.session_state.tab = "Mappage des Colonnes"
                    st.rerun()
                
            except Exception as e:
                st.error(f"Erreur lors du chargement du fichier: {e}")
    
    elif import_method == "Copier-coller des données":
        pasted_data = st.text_area(
            "Collez vos données (format CSV ou tableau séparé par des tabulations):",
            height=200,
            key="pasted_data"
        )
        
        separator = st.selectbox(
            "Séparateur:",
            [",", ";", "Tab"],
            key="paste_separator"
        )
        
        if st.button("Traiter les données"):
            if pasted_data:
                sep_dict = {",": ",", ";": ";", "Tab": "\t"}
                try:
                    df = pd.read_csv(StringIO(pasted_data), sep=sep_dict[separator])
                    st.session_state.data = df
                    st.success(f"Données traitées avec succès! {len(df)} lignes et {len(df.columns)} colonnes.")
                    st.write("Aperçu des données:")
                    st.dataframe(df.head())
                    
                    # Bouton pour continuer
                    if st.button("Continuer vers le mappage des colonnes", key="continue_to_mapping_paste"):
                        st.session_state.tab = "Mappage des Colonnes"
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"Erreur lors du traitement des données: {e}")
            else:
                st.warning("Veuillez coller des données avant de les traiter.")
    
    elif import_method == "Utiliser les données d'exemple":
        control_type = st.session_state.control_type
        
        if control_type == "Standards CRM":
            example_data = get_crm_example_data()
            st.code(example_data, language="text")
            
            if st.button("Utiliser ces données d'exemple", key="use_crm_example_import"):
                df = pd.read_csv(StringIO(example_data))
                st.session_state.data = df
                st.success(f"Données d'exemple chargées avec succès! {len(df)} lignes et {len(df.columns)} colonnes.")
                st.write("Aperçu des données:")
                st.dataframe(df.head())
                
                # Stocker temporairement les valeurs recommandées
                st.session_state.temp_values = {
                    'ref_value': 1.25,
                    'ref_stddev': 0.05,
                    'tolerance_percent': 10.0
                }
                
                # Bouton pour continuer
                if st.button("Continuer vers le mappage des colonnes", key="continue_to_mapping_example_crm"):
                    st.session_state.tab = "Mappage des Colonnes"
                    st.rerun()
        
        elif control_type == "Blancs":
            example_data = get_blank_example_data()
            st.code(example_data, language="text")
            
            if st.button("Utiliser ces données d'exemple", key="use_blank_example_import"):
                df = pd.read_csv(StringIO(example_data))
                st.session_state.data = df
                st.success(f"Données d'exemple chargées avec succès! {len(df)} lignes et {len(df.columns)} colonnes.")
                st.write("Aperçu des données:")
                st.dataframe(df.head())
                
                # Bouton pour continuer
                if st.button("Continuer vers le mappage des colonnes", key="continue_to_mapping_example_blank"):
                    st.session_state.tab = "Mappage des Colonnes"
                    st.rerun()
        
        elif control_type == "Duplicatas (nuage de points et régression)":
            example_data = get_duplicate_example_data()
            st.code(example_data, language="text")
            
            if st.button("Utiliser ces données d'exemple", key="use_duplicate_example_import"):
                df = pd.read_csv(StringIO(example_data))
                st.session_state.data = df
                st.success(f"Données d'exemple chargées avec succès! {len(df)} lignes et {len(df.columns)} colonnes.")
                st.write("Aperçu des données:")
                st.dataframe(df.head())
                
                # Bouton pour continuer
                if st.button("Continuer vers le mappage des colonnes", key="continue_to_mapping_example_duplicate"):
                    st.session_state.tab = "Mappage des Colonnes"
                    st.rerun()
    
    # Ajouter des boutons de navigation
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("← Revenir au Type de Contrôle"):
            st.session_state.tab = "Type de Contrôle"
            st.rerun()

elif st.session_state.tab == "Mappage des Colonnes":
    # ONGLET 3: MAPPAGE DES COLONNES
    st.header("Mappage des Colonnes")
    
    if st.session_state.data is None:
        st.warning("Aucune donnée n'a été importée. Veuillez d'abord importer des données dans l'étape 'Importation des Données'.")
        
        if st.button("← Revenir à l'Importation des Données"):
            st.session_state.tab = "Importation des Données"
            st.rerun()
    else:
        df = st.session_state.data
        
        st.write("Associez les colonnes de vos données aux champs requis par l'application:")
        
        # Création du formulaire de mappage
        mapping_form = st.form("column_mapping_form")
        
        with mapping_form:
            mapping_dict = {}
            
            for field_id, field_name in st.session_state.required_fields.items():
                mapping_dict[field_id] = st.selectbox(
                    f"Champ '{field_name}':",
                    options=["-- Sélectionner une colonne --"] + list(df.columns),
                    key=f"mapping_{field_id}"
                )
            
            submit_button = st.form_submit_button("Appliquer le mappage")
        
        if submit_button:
            # Vérifier que toutes les colonnes ont été mappées
            if all(col != "-- Sélectionner une colonne --" for col in mapping_dict.values()):
                # Créer un dictionnaire de mappage inversé
                inverse_mapping = {v: k for k, v in mapping_dict.items()}
                
                # Créer un DataFrame mappé
                mapped_data = pd.DataFrame()
                
                for source_col, target_field in inverse_mapping.items():
                    mapped_data[target_field] = df[source_col]
                
                st.session_state.mapped_data = mapped_data
                st.session_state.column_mapping = mapping_dict
                st.session_state.mapping_done = True
                
                st.success("Mappage des colonnes effectué avec succès!")
                st.write("Aperçu des données mappées:")
                st.dataframe(mapped_data.head())
            else:
                st.error("Veuillez associer toutes les colonnes requises.")
        
        # Afficher ces boutons seulement si le mappage a été effectué avec succès
        if st.session_state.mapping_done:
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("← Revenir à l'Importation des Données"):
                    st.session_state.tab = "Importation des Données"
                    st.rerun()
            with col2:
                if st.button("Continuer vers l'Analyse →"):
                    st.session_state.tab = "Analyse"
                    st.rerun()
        else:
            # Sinon, afficher seulement le bouton retour
            if st.button("← Revenir à l'Importation des Données"):
                st.session_state.tab = "Importation des Données"
                st.rerun()

elif st.session_state.tab == "Analyse":
    # ONGLET 4: ANALYSE
    st.header("Analyse des Données")
    
    if not st.session_state.mapping_done:
        st.warning("Veuillez d'abord mapper les colonnes de vos données dans l'étape 'Mappage des Colonnes'.")
        
        if st.button("← Revenir au Mappage des Colonnes"):
            st.session_state.tab = "Mappage des Colonnes"
            st.rerun()
    else:
        data = st.session_state.mapped_data
        control_type = st.session_state.control_type
        graph_title = st.session_state.graph_title
        
        # Analyse selon le type de contrôle
        if control_type == "Standards CRM":
            if st.button("Générer la Carte de Contrôle", key="generate_crm"):
                # Préparation des données
                id_column = "sample_id"
                value_column = "measured_value"
                
                analysis_data = data[[id_column, value_column]].copy()
                analysis_data = analysis_data.dropna()
                analysis_data[value_column] = pd.to_numeric(analysis_data[value_column], errors='coerce')
                analysis_data = analysis_data.dropna()
                
                if analysis_data.empty:
                    st.error("Aucune donnée numérique valide trouvée pour l'analyse.")
                else:
                    # Récupération des paramètres
                    reference_value = st.session_state.reference_value
                    tolerance_type = st.session_state.tolerance_type
                    
                    if tolerance_type == "Pourcentage (%)":
                        tolerance_value = st.session_state.tolerance_percent
                    else:
                        tolerance_value = st.session_state.tolerance_stddev
                        
                    reference_stddev = st.session_state.reference_stddev if 'reference_stddev' in st.session_state else 0
                    
                    # Calcul des limites
                    lower_limit, upper_limit = calculate_crm_limits(
                        reference_value,
                        tolerance_type,
                        tolerance_value,
                        reference_stddev
                    )
                    
                    if lower_limit is not None and upper_limit is not None:
                        # Statistiques
                        values = analysis_data[value_column].values
                        mean = np.mean(values)
                        std_dev = np.std(values)
                        min_val = np.min(values)
                        max_val = np.max(values)
                        
                        # Récupérer le nom original de la colonne pour le titre
                        original_id_column = st.session_state.column_mapping.get('sample_id', 'Identifiant')
                        original_value_column = st.session_state.column_mapping.get('measured_value', 'Valeur')
                        
                        # Création du graphique avec Plotly
                        fig = go.Figure()
                        
                        # Données mesurées
                        fig.add_trace(go.Scatter(
                            x=analysis_data[id_column],
                            y=analysis_data[value_column],
                            mode='lines+markers',
                            name='Valeur mesurée',
                            line=dict(color='rgb(75, 192, 192)', width=2),
                            marker=dict(size=8)
                        ))
                        
                        # Valeur de référence
                        fig.add_trace(go.Scatter(
                            x=analysis_data[id_column],
                            y=[reference_value] * len(analysis_data),
                            mode='lines',
                            name='Valeur référence',
                            line=dict(color='rgb(54, 162, 235)', width=2, dash='dash')
                        ))
                        
                        # Limites
                        fig.add_trace(go.Scatter(
                            x=analysis_data[id_column],
                            y=[upper_limit] * len(analysis_data),
                            mode='lines',
                            name='Limite supérieure',
                            line=dict(color='rgb(255, 99, 132)', width=2, dash='dash')
                        ))
                        
                        fig.add_trace(go.Scatter(
                            x=analysis_data[id_column],
                            y=[lower_limit] * len(analysis_data),
                            mode='lines',
                            name='Limite inférieure',
                            line=dict(color='rgb(255, 99, 132)', width=2, dash='dash')
                        ))
                        
                        # Mise en forme
                        fig.update_layout(
                            title=f"{graph_title} - {original_value_column}",
                            xaxis_title=original_id_column,
                            yaxis_title=original_value_column,
                            height=600,
                            hovermode="closest"
                        )
                        
                        # Stocker le graphique pour l'exportation
                        st.session_state.current_fig = fig
                        
                        # Afficher le graphique
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Tableau des statistiques
                        st.subheader("Statistiques")
                        
                        stats_col1, stats_col2 = st.columns(2)
                        
                        # Créer un dictionnaire pour les statistiques
                        stats_dict = {
                            "Valeur de référence": f"{reference_value:.4f}",
                            "Moyenne": f"{mean:.4f}",
                            "Écart-type": f"{std_dev:.4f}",
                            "Min": f"{min_val:.4f}",
                            "Max": f"{max_val:.4f}"
                        }
                        
                        if reference_stddev > 0:
                            stats_dict["Écart-type de référence"] = f"{reference_stddev:.4f}"
                        
                        if tolerance_type == "Pourcentage (%)":
                            stats_dict["Tolérance"] = f"{tolerance_value:.2f}%"
                        else:
                            stats_dict["Tolérance"] = f"{tolerance_value:.1f} × écart-type"
                        
                        # Stocker les statistiques pour l'exportation
                        st.session_state.current_stats = stats_dict
                        
                        with stats_col1:
                            st.markdown(f"**Valeur de référence:** {reference_value:.4f}")
                            
                            if reference_stddev > 0:
                                st.markdown(f"**Écart-type de référence:** {reference_stddev:.4f}")
                            
                            if tolerance_type == "Pourcentage (%)":
                                st.markdown(f"**Tolérance:** {tolerance_value:.2f}%")
                            else:
                                st.markdown(f"**Tolérance:** {tolerance_value:.1f} × écart-type")
                        
                        with stats_col2:
                            st.markdown(f"**Moyenne:** {mean:.4f}")
                            st.markdown(f"**Écart-type:** {std_dev:.4f}")
                            st.markdown(f"**Min:** {min_val:.4f}")
                            st.markdown(f"**Max:** {max_val:.4f}")
                        
                        # Tableau de données
                        st.subheader("Résultats détaillés")
                        
                        # Création d'un DataFrame avec les résultats
                        results_df = analysis_data.copy()
                        results_df['Écart (%)'] = ((results_df[value_column] - reference_value) / reference_value) * 100
                        
                        if reference_stddev > 0:
                            results_df['Z-score'] = (results_df[value_column] - reference_value) / reference_stddev
                        
                        results_df['Statut'] = results_df[value_column].apply(
                            lambda x: 'OK' if lower_limit <= x <= upper_limit else 'Hors limites'
                        )
                        
                        # Renommer les colonnes du tableau de résultats avec les noms originaux
                        display_df = results_df.copy()
                        display_df.rename(columns={
                            'sample_id': original_id_column,
                            'measured_value': original_value_column
                        }, inplace=True)
                        
                        # Stocker les résultats pour l'exportation
                        st.session_state.current_results = display_df
                        
                        # Afficher le tableau avec coloration conditionnelle
                        st.dataframe(display_df.style.apply(
                            lambda x: ['background-color: #ffcccc' if v == 'Hors limites' else '' for v in x],
                            subset=['Statut']
                        ))
                        
                        # Boutons de navigation
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("← Revenir au Mappage des Colonnes", key="back_to_mapping_from_analysis"):
                                st.session_state.tab = "Mappage des Colonnes"
                                st.rerun()
                        with col2:
                            if st.button("Continuer vers l'Exportation →", key="go_to_export_from_analysis"):
                                st.session_state.tab = "Export"
                                st.rerun()
            
            # Si le graphique a déjà été généré, afficher aussi les boutons de navigation
            if st.session_state.current_fig is not None and 'current_results' in st.session_state and st.session_state.current_results is not None:
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("← Revenir au Mappage des Colonnes", key="back_to_mapping_again"):
                        st.session_state.tab = "Mappage des Colonnes"
                        st.rerun()
                with col2:
                    if st.button("Continuer vers l'Exportation →", key="go_to_export_again"):
                        st.session_state.tab = "Export"
                        st.rerun()
            else:
                # Sinon, afficher seulement le bouton retour
                if st.button("← Revenir au Mappage des Colonnes"):
                    st.session_state.tab = "Mappage des Colonnes"
                    st.rerun()
                
        elif control_type == "Duplicatas (nuage de points et régression)":
            if st.button("Générer la Carte de Contrôle", key="generate_duplicates"):
                # Préparation des données
                original_column = "original_value"
                replicate_column = "duplicate_value"
                
                analysis_data = data[[original_column, replicate_column]].copy()
                analysis_data = analysis_data.dropna()
                analysis_data[original_column] = pd.to_numeric(analysis_data[original_column], errors='coerce')
                analysis_data[replicate_column] = pd.to_numeric(analysis_data[replicate_column], errors='coerce')
                analysis_data = analysis_data.dropna()
                
                if analysis_data.empty:
                    st.error("Aucune donnée numérique valide trouvée pour l'analyse.")
                else:
                    # Calcul de la régression linéaire
                    x = analysis_data[original_column].values
                    y = analysis_data[replicate_column].values
                    
                    slope, intercept = np.polyfit(x, y, 1)
                    r = np.corrcoef(x, y)[0, 1]
                    
                    # Calcul des statistiques
                    differences = np.abs(y - x)
                    mean_diff = np.mean(differences)
                    
                    relative_diff = np.abs(y - x) / ((x + y) / 2) * 100
                    mean_relative_diff = np.nanmean(relative_diff)
                    
                    # Récupérer les noms originaux des colonnes pour le titre
                    original_value_name = st.session_state.column_mapping.get('original_value', 'Valeur originale')
                    duplicate_value_name = st.session_state.column_mapping.get('duplicate_value', 'Valeur dupliquée')
                    
                    # Création du graphique avec Plotly
                    fig = go.Figure()
                    
                    # Nuage de points
                    fig.add_trace(go.Scatter(
                        x=analysis_data[original_column],
                        y=analysis_data[replicate_column],
                        mode='markers',
                        name='Duplicatas',
                        marker=dict(
                            color='rgb(75, 192, 192)',
                            size=10,
                            opacity=0.8
                        )
                    ))
                    
                    # Ligne de régression
                    x_range = np.linspace(min(x), max(x), 100)
                    y_pred = slope * x_range + intercept
                    
                    fig.add_trace(go.Scatter(
                        x=x_range,
                        y=y_pred,
                        mode='lines',
                        name=f'Régression linéaire (y = {slope:.4f}x + {intercept:.4f})',
                        line=dict(color='rgb(255, 99, 132)', width=2)
                    ))
                    
                    # Ligne d'égalité parfaite (y = x)
                    fig.add_trace(go.Scatter(
                        x=x_range,
                        y=x_range,
                        mode='lines',
                        name='Ligne d\'égalité (y=x)',
                        line=dict(color='rgb(54, 162, 235)', width=2, dash='dash')
                    ))
                    
                    # Mise en forme
                    fig.update_layout(
                        title=f"{graph_title} - {original_value_name} vs {duplicate_value_name}",
                        xaxis_title=original_value_name,
                        yaxis_title=duplicate_value_name,
                        height=600,
                        hovermode="closest"
                    )
                    
                    # Stocker le graphique pour l'exportation
                    st.session_state.current_fig = fig
                    
                    # Afficher le graphique
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tableau des statistiques
                    st.subheader("Statistiques")
                    
                    # Créer un dictionnaire pour les statistiques
                    stats_dict = {
                        "Équation de régression": f"y = {slope:.4f}x + {intercept:.4f}",
                        "Coefficient de corrélation (R²)": f"{r*r:.4f}",
                        "Différence absolue moyenne": f"{mean_diff:.4f}",
                        "Différence relative moyenne": f"{mean_relative_diff:.2f}%"
                    }
                    
                    # Stocker les statistiques pour l'exportation
                    st.session_state.current_stats = stats_dict
                    
                    st.markdown(f"**Équation de régression:** y = {slope:.4f}x + {intercept:.4f}")
                    st.markdown(f"**Coefficient de corrélation (R²):** {r*r:.4f}")
                    st.markdown(f"**Différence absolue moyenne:** {mean_diff:.4f}")
                    st.markdown(f"**Différence relative moyenne:** {mean_relative_diff:.2f}%")
                    
                    # Tableau de données
                    st.subheader("Résultats détaillés")
                    
                    # Création d'un DataFrame avec les résultats
                    results_df = analysis_data.copy()
                    results_df['Diff. Abs.'] = np.abs(results_df[replicate_column] - results_df[original_column])
                    results_df['Diff. Rel. (%)'] = np.abs(results_df[replicate_column] - results_df[original_column]) / ((results_df[original_column] + results_df[replicate_column]) / 2) * 100
                    
                    # Renommer les colonnes pour affichage
                    display_df = results_df.copy()
                    display_df.rename(columns={
                        'original_value': original_value_name,
                        'duplicate_value': duplicate_value_name
                    }, inplace=True)
                    
                    # Stocker les résultats pour l'exportation
                    st.session_state.current_results = display_df
                    
                    # Afficher le tableau
                    st.dataframe(display_df)
                    
                    # Boutons de navigation
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("← Revenir au Mappage des Colonnes", key="back_to_mapping_dup"):
                            st.session_state.tab = "Mappage des Colonnes"
                            st.rerun()
                    with col2:
                        if st.button("Continuer vers l'Exportation →", key="go_to_export_dup"):
                            st.session_state.tab = "Export"
                            st.rerun()
            
            # Si le graphique a déjà été généré, afficher aussi les boutons de navigation
            if st.session_state.current_fig is not None and 'current_results' in st.session_state and st.session_state.current_results is not None:
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("← Revenir au Mappage des Colonnes", key="back_to_mapping_dup_again"):
                        st.session_state.tab = "Mappage des Colonnes"
                        st.rerun()
                with col2:
                    if st.button("Continuer vers l'Exportation →", key="go_to_export_dup_again"):
                        st.session_state.tab = "Export"
                        st.rerun()
            else:
                # Sinon, afficher seulement le bouton retour
                if st.button("← Revenir au Mappage des Colonnes"):
                    st.session_state.tab = "Mappage des Colonnes"
                    st.rerun()
                
        elif control_type == "Blancs":
            if st.button("Générer la Carte de Contrôle", key="generate_blanks"):
                # Préparation des données
                id_column = "sample_id"
                value_column = "measured_value"
                
                analysis_data = data[[id_column, value_column]].copy()
                analysis_data = analysis_data.dropna()
                analysis_data[value_column] = pd.to_numeric(analysis_data[value_column], errors='coerce')
                analysis_data = analysis_data.dropna()
                
                if analysis_data.empty:
                    st.error("Aucune donnée numérique valide trouvée pour l'analyse.")
                else:
                    # Récupérer les noms originaux des colonnes pour le titre
                    original_id_column = st.session_state.column_mapping.get('sample_id', 'Identifiant')
                    original_value_column = st.session_state.column_mapping.get('measured_value', 'Valeur')
                
                    # Calcul des statistiques
                    values = analysis_data[value_column].values
                    mean = np.mean(values)
                    std_dev = np.std(values)
                    min_val = np.min(values)
                    max_val = np.max(values)
                    
                    # Limites de détection estimées
                    lod = mean + 3 * std_dev
                    
                    # Création du graphique avec Plotly
                    fig = go.Figure()
                    
                    # Données mesurées
                    fig.add_trace(go.Scatter(
                        x=analysis_data[id_column],
                        y=analysis_data[value_column],
                        mode='lines+markers',
                        name='Valeur mesurée',
                        line=dict(color='rgb(75, 192, 192)', width=2),
                        marker=dict(size=8)
                    ))
                    
                    # Moyenne
                    fig.add_trace(go.Scatter(
                        x=analysis_data[id_column],
                        y=[mean] * len(analysis_data),
                        mode='lines',
                        name='Moyenne',
                        line=dict(color='rgb(54, 162, 235)', width=2, dash='dash')
                    ))
                    
                    # Limite de détection
                    fig.add_trace(go.Scatter(
                        x=analysis_data[id_column],
                        y=[lod] * len(analysis_data),
                        mode='lines',
                        name='Limite de détection (LOD)',
                        line=dict(color='rgb(255, 99, 132)', width=2, dash='dash')
                    ))
                    
                    # Mise en forme
                    fig.update_layout(
                        title=f"{graph_title} - {original_value_column}",
                        xaxis_title=original_id_column,
                        yaxis_title=original_value_column,
                        height=600,
                        hovermode="closest"
                    )
                    
                    # Stocker le graphique pour l'exportation
                    st.session_state.current_fig = fig
                    
                    # Afficher le graphique
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tableau des statistiques
                    st.subheader("Statistiques")
                    
                    # Créer un dictionnaire pour les statistiques
                    stats_dict = {
                        "Moyenne": f"{mean:.4f}",
                        "Écart-type": f"{std_dev:.4f}",
                        "Min": f"{min_val:.4f}",
                        "Max": f"{max_val:.4f}",
                        "Limite de détection estimée (LOD)": f"{lod:.4f}"
                    }
                    
                    # Stocker les statistiques pour l'exportation
                    st.session_state.current_stats = stats_dict
                    
                    st.markdown(f"**Moyenne:** {mean:.4f}")
                    st.markdown(f"**Écart-type:** {std_dev:.4f}")
                    st.markdown(f"**Min:** {min_val:.4f}")
                    st.markdown(f"**Max:** {max_val:.4f}")
                    st.markdown(f"**Limite de détection estimée (LOD):** {lod:.4f}")
                    
                    # Tableau de données
                    st.subheader("Résultats détaillés")
                    
                    # Création d'un DataFrame avec les résultats
                    results_df = analysis_data.copy()
                    results_df['Statut'] = results_df[value_column].apply(
                        lambda x: 'OK' if x <= lod else 'Élevé'
                    )
                    
                    # Renommer les colonnes pour affichage
                    display_df = results_df.copy()
                    display_df.rename(columns={
                        'sample_id': original_id_column,
                        'measured_value': original_value_column
                    }, inplace=True)
                    
                    # Stocker les résultats pour l'exportation
                    st.session_state.current_results = display_df
                    
                    # Afficher le tableau avec coloration conditionnelle
                    st.dataframe(display_df.style.apply(
                        lambda x: ['background-color: #ffcccc' if v == 'Élevé' else '' for v in x],
                        subset=['Statut']
                    ))
                    
                    # Boutons de navigation
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("← Revenir au Mappage des Colonnes", key="back_to_mapping_blank"):
                            st.session_state.tab = "Mappage des Colonnes"
                            st.rerun()
                    with col2:
                        if st.button("Continuer vers l'Exportation →", key="go_to_export_blank"):
                            st.session_state.tab = "Export"
                            st.rerun()
            
            # Si le graphique a déjà été généré, afficher aussi les boutons de navigation
            if st.session_state.current_fig is not None and 'current_results' in st.session_state and st.session_state.current_results is not None:
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("← Revenir au Mappage des Colonnes", key="back_to_mapping_blank_again"):
                        st.session_state.tab = "Mappage des Colonnes"
                        st.rerun()
                with col2:
                    if st.button("Continuer vers l'Exportation →", key="go_to_export_blank_again"):
                        st.session_state.tab = "Export"
                        st.rerun()
            else:
                # Sinon, afficher seulement le bouton retour
                if st.button("← Revenir au Mappage des Colonnes"):
                    st.session_state.tab = "Mappage des Colonnes"
                    st.rerun()

elif st.session_state.tab == "Export":
    # ONGLET 5: EXPORT
    st.header("Exportation des Résultats")
    
    if 'current_fig' not in st.session_state or st.session_state.current_fig is None:
        st.warning("Aucun résultat à exporter. Veuillez d'abord générer une analyse dans l'étape 'Analyse'.")
        
        if st.button("← Revenir à l'Analyse"):
            st.session_state.tab = "Analyse"
            st.rerun()
    else:
        st.subheader("Personnalisation de l'exportation")
        
        # Options d'exportation
        export_title = st.text_input(
            "Titre du rapport:",
            value=st.session_state.graph_title,
            key="export_title_input"
        )
        
        export_author = st.text_input(
            "Auteur du rapport:",
            value=st.session_state.report_author,
            key="export_author_input"
        )
        
        export_format = st.radio(
            "Format d'exportation:",
            ["PNG", "PDF", "CSV"],
            key="export_format"
        )
        
        # Aperçu du graphique
        st.subheader("Aperçu du graphique")
        st.plotly_chart(st.session_state.current_fig, use_container_width=True)
        
        # Bouton d'exportation
        if st.button("Exporter les résultats"):
            if export_format == "PNG":
                # Exporter le graphique en PNG
                img_bytes = export_plotly_to_png(st.session_state.current_fig)
                
                # Créer un lien de téléchargement
                b64 = base64.b64encode(img_bytes).decode()
                href = f'<a href="data:image/png;base64,{b64}" download="geoqaqc_graph.png">Télécharger le graphique (PNG)</a>'
                st.markdown(href, unsafe_allow_html=True)
                
                st.success("Graphique exporté en PNG avec succès!")
                
            elif export_format == "PDF":
                # Exporter le rapport en PDF
                try:
                    pdf_bytes = export_to_pdf(
                        export_title,
                        st.session_state.current_fig,
                        st.session_state.current_stats,
                        st.session_state.current_results,
                        export_author
                    )
                    
                    # Créer un lien de téléchargement
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="geoqaqc_report.pdf">Télécharger le rapport (PDF)</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                    st.success("Rapport exporté en PDF avec succès!")
                except Exception as e:
                    st.error(f"Erreur lors de l'exportation en PDF: {e}")
                
            elif export_format == "CSV":
                # Exporter les données en CSV
                if st.session_state.current_results is not None:
                    csv = st.session_state.current_results.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="geoqaqc_results.csv">Télécharger les résultats (CSV)</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                    st.success("Résultats exportés en CSV avec succès!")
                else:
                    st.error("Aucun résultat à exporter.")
        
        # Bouton de retour
        if st.button("← Revenir à l'Analyse"):
            st.session_state.tab = "Analyse"
            st.rerun()

# Footer
st.markdown("---")
st.markdown(f"**GeoQAQC** © 2025 - Développé par {st.session_state.report_author}")