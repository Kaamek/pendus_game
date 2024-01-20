import streamlit as st
from sqlalchemy import create_engine, text, delete, Table, MetaData
import hashlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
import pandas as pd
import random



def send_email(to_email, username, firstname, lastname, interest):
    # Configurations SMTP (exemple avec Gmail)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "ibrahimassebbane@gmail.com"
    smtp_password = "ykht amvw aqvc ditx"

    # Création du message
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = smtp_user
    msg['Subject'] = "Nouvelle inscription"

    body = f"Nom d'utilisateur: {username}\nPrénom: {firstname}\nPrénom: {firstname}\nNom: {lastname}\nRaison(s): {interest}"
    msg.attach(MIMEText(body, 'plain'))

    # Connexion au serveur et envoi de l'email
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_user, smtp_password)
    server.send_message(msg)
    server.quit()

# Fonctions pour le hachage et la vérification des mots de passe
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

def get_db_connection():
    engine = create_engine("sqlite:///users.db")
    conn = engine.connect()
    return conn


# Connexion à la base de données
engine = create_engine("sqlite:///users.db")
conn = engine.connect()

# Création de la table des utilisateurs
conn.execute(text('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT,
        email TEXT, 
        firstname TEXT, 
        lastname TEXT, 
        password TEXT,
        interest TEXT
    );
'''))

# Initialisation de la session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'show_register' not in st.session_state:
    st.session_state['show_register'] = False

if 'message' not in st.session_state:
    st.session_state['message'] = ""

if 'lettre_temp' not in st.session_state:
    st.session_state['lettre_temp'] = ""

    

# Afficher un message (si présent) et le réinitialiser
if st.session_state['message']:
    st.success(st.session_state['message'])
    st.session_state['message'] = ""



def register():
    with st.container():
        st.title("Créer un nouveau compte")
        new_username = st.text_input("Nom d'utilisateur", key="new_username")
        new_email = st.text_input("Email", key="new_email")
        new_firstname = st.text_input("Prénom", key="new_firstname")
        new_lastname = st.text_input("Nom", key="new_lastname")
        new_password = st.text_input("Mot de passe", type='password', key="new_password")
        interest = st.text_input("Pour quelle(s) raison voulez-vous accéder à l'application ?", key="interest")
        
        if st.button("S'inscrire", key="register", type='primary'):
            # Validation de l'email
            if "@" not in new_email :
                st.error("L'adresse email doit contenir un '@' et se terminer par '.com' ou '.fr'")
                return

            # Validation du mot de passe
            if len(new_password) < 8 or not re.search("[a-zA-Z]", new_password) or not re.search("[0-9]", new_password):
                st.error("Le mot de passe doit contenir au moins 8 caractères, incluant des chiffres et des lettres.")
                return

            # Si les validations sont passées, insérer dans la base de données
            hashed_new_password = make_hashes(new_password)
            try:
                conn.execute(text('''
                    INSERT INTO users (username, email, firstname, lastname, password, interest) 
                    VALUES (:username, :email, :firstname, :lastname, :password, :interest);
                '''), {'username': new_username, 'email': new_email, 'firstname': new_firstname, 'lastname': new_lastname, 'password': hashed_new_password, 'interest': interest})
                send_email(new_email, new_username, new_firstname, new_lastname, interest)
                conn.commit()
                st.session_state['message'] = "Compte créé avec succès !"
                st.session_state['show_register'] = False
                st.rerun()
            except Exception as e:
                st.error("Une erreur s'est produite lors de la création du compte. Veuillez réessayer............")
                print(e)

def connect():
    with st.container():
        st.title("Connexion")
        username = st.text_input("Nom d'utilisateur", key="username")
        password = st.text_input("Mot de passe", type='password', key="password")
        if st.button("Se connecter", key="login", type="primary"):
            result = conn.execute(text("SELECT * FROM users WHERE username=:username"), {'username': username})
            user = result.fetchone()
            if user and check_hashes(password, user[5]):  # Utilisez l'indice numérique pour accéder au mot de passe
                st.session_state['logged_in'] = True
                st.rerun()
                return username
            else:
                st.error("Identifiant ou mot de passe incorrect")
        if not st.session_state['show_register']:    
            if st.button("Créer un compte", key="go_to_register"):
                st.session_state['show_register'] = True
                st.rerun()

def delete_user():
    current_user_id = st.session_state['current_user_id']
    if current_user_id:
        delete_query = text("DELETE FROM users WHERE id=:id")
        conn.execute(delete_query, {'id': current_user_id})
        conn.commit()
        st.success("Compte supprimé avec succès.")
        st.session_state['logged_in'] = False
        st.session_state['show_register'] = False
        st.experimental_rerun()
  

# Fonction pour choisir un mot aléatoire parmi la liste
def choisir_mot_aleatoire():
    with open('listes_mots.txt', 'r', encoding='utf-8') as file:
        mots_en_francais = file.read().splitlines()
    return random.choice(mots_en_francais).upper()

# Fonction pour afficher le mot caché
def afficher_mot_cache(mot, lettres_trouvees):
    return ''.join([lettre if lettre in lettres_trouvees else '.' for lettre in mot])

# Fonction principale du jeu du pendu
def pendu_game():
    st.subheader("Jeu du Pendu")

    # Initialisation ou récupération de l'état de session
    if 'mot_a_deviner' not in st.session_state or st.sidebar.button("Nouveau Mot"):
        st.session_state['mot_a_deviner'] = choisir_mot_aleatoire()
        st.session_state['lettres_trouvees'] = set()
        st.session_state['tentatives'] = 6

    mot_a_deviner = st.session_state['mot_a_deviner']
    lettres_trouvees = st.session_state['lettres_trouvees']

    # Afficher le mot caché
    mot_cache = afficher_mot_cache(mot_a_deviner, lettres_trouvees)
    st.markdown(f"<h3 style='text-align: left; font-weight: bold;'>Mot à deviner : {mot_cache}</h3>", unsafe_allow_html=True)

    # Afficher les lettres déjà entrées
    if lettres_trouvees:
        st.write("Lettres déjà tentées :", ", ".join(sorted(lettres_trouvees)))

    # Gérer la saisie de la lettre
    lettre_input = st.text_input("Devinez une lettre :", key="lettre_input").strip().upper()

    if st.button("Soumettre"):
        if lettre_input and len(lettre_input) == 1 and lettre_input.isalpha():
            lettres_trouvees.add(lettre_input)  # Ajouter la lettre essayée à l'ensemble
            st.session_state['lettres_trouvees'] = lettres_trouvees

            if lettre_input in mot_a_deviner:
                if all(lettre in lettres_trouvees for lettre in mot_a_deviner):
                    st.success(f"Félicitations, vous avez deviné le mot : {mot_a_deviner}!")
            else:
                st.session_state['tentatives'] -= 1
                if st.session_state['tentatives'] == 0:
                    st.error(f"Jeu terminé. Le mot était : {mot_a_deviner}.")
                else:
                    st.error("La lettre n'est pas dans le mot. Essayez à nouveau.")
            st.rerun()
        else:
            st.warning("Veuillez entrer une seule lettre alphabétique.")
    



def main():
    st.subheader("Bienvenue dans l'application !")
    conn = get_db_connection()

    if 'username' in st.session_state:
        # Récupérer l'ID de l'utilisateur actuel
        current_user = st.session_state['username']
        user_data = conn.execute(text("SELECT * FROM users WHERE username=:username"), {'username': current_user}).fetchone()
        if user_data:
            st.write(f"Vos informations : {user_data}")
            st.session_state['current_user_id'] = user_data[0]  # Stockez l'ID dans st.session_state

    if 'current_user_id' in st.session_state and st.session_state['current_user_id']:
        # Bouton de suppression dans la barre latérale
        if st.sidebar.button("Supprimer mon compte"):
            delete_user()
    
    # Exécutez le jeu du pendu
    pendu_game()


    








st.cache_data.clear()

# Afficher un message temporaire
if st.session_state['message']:
    with st.empty():  # Utiliser un conteneur vide
        st.success(st.session_state['message'])  # Afficher le message
        time.sleep(2)  # Attendre 2 secondes
        st.session_state['message'] = ""  # Effacer le message après 2 secondes
        st.rerun()


# Vue d'inscription
if not st.session_state['logged_in'] and st.session_state['show_register']:
    # Appel de la fonction pour l'inscription
    register()

# Vue de connexion
elif not st.session_state['logged_in']:
    connect()

# Contenu principal de l'application
elif st.session_state['logged_in']:
    main()


                        
                
                



# Fermer la connexion à la base de données
conn.close()