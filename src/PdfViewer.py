import streamlit as st
from pdf2image import convert_from_path

class PDFViewer:
    def __init__(self, source_data, file_paths):
        self.source_data = source_data
        self.file_paths = file_paths
        self.initialize_states()

    def initialize_states(self):
        """Initialise les états de session Streamlit."""
        if "file_choice" not in st.session_state:
            st.session_state.file_choice = list(self.source_data.keys())[0]  # Premier document
        if "page_number" not in st.session_state:
            st.session_state.page_number = 1  # Première page par défaut

    def update_file_choice(self, new_file_choice):
        """Met à jour le fichier sélectionné et réinitialise la page."""
        if new_file_choice != st.session_state.file_choice:
            st.session_state.file_choice = new_file_choice
            st.session_state.page_number = 1  # Réinitialise la page à 1

    def update_page_number(self, new_page_number):
        """Met à jour le numéro de page sélectionné."""
        st.session_state.page_number = new_page_number

    def get_all_pages(self, file_choice):
        """Retourne toutes les pages disponibles pour le fichier donné."""
        pages_list = self.source_data[file_choice]
        all_pages = []
        for page_range in pages_list:
            if "-" in page_range:
                start, end = map(int, page_range.split("-"))
                all_pages.extend(range(start, end + 1))
            else:
                all_pages.append(int(page_range))
        return sorted(set(all_pages))

    def display(self):
        """Affiche l'interface utilisateur et la page PDF."""
        # Afficher le sélecteur de fichiers
        file_choice = st.selectbox(
            "Choisissez un fichier PDF",
            options=list(self.source_data.keys()),
            index=list(self.source_data.keys()).index(st.session_state.file_choice),
            on_change=self.update_file_choice,
            args=(st.session_state.file_choice,),
        )

        # Afficher la navigation et la page PDF
        self.show_navigation(file_choice)
        self.show_pdf(file_choice)

    def show_navigation(self, file_choice):
        """Affiche les contrôles de navigation."""
        all_pages = self.get_all_pages(file_choice)

        # Si aucune page n'est disponible
        if not all_pages:
            st.warning("Aucune page disponible pour ce fichier.")
            return

        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Précédente"):
                if st.session_state.page_number > min(all_pages):
                    self.update_page_number(st.session_state.page_number - 1)
        with col3:
            if st.button("➡️ Suivante"):
                if st.session_state.page_number < max(all_pages):
                    self.update_page_number(st.session_state.page_number + 1)

        # Slider pour navigation rapide
        if len(all_pages) > 1:
            new_page = st.slider(
                "Aller à la page :",
                min_value=min(all_pages),
                max_value=max(all_pages),
                value=st.session_state.page_number,
                step=1,
                on_change=self.update_page_number,
                args=(st.session_state.page_number,),
            )

    def show_pdf(self, file_choice):
        """Affiche la page PDF sélectionnée."""
        all_pages = self.get_all_pages(file_choice)
        if not all_pages:
            return

        # Limiter le numéro de page
        page_number = max(min(st.session_state.page_number, max(all_pages)), min(all_pages))

        # Convertir et afficher la page PDF
        try:
            file_path = self.file_paths[file_choice]
            pages = convert_from_path(
                file_path,
                first_page=page_number,
                last_page=page_number,
            )
            st.image(pages[0], caption=f"Page {page_number} du fichier {file_choice}")
        except Exception as e:
            st.error(f"Erreur lors de l'affichage de la page : {e}")
