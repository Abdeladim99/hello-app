import streamlit as st
import pymysql
import pandas as pd

# Fonction pour formater la date comme en Blue Open Studio
def format_date(date_input):
    date_str = date_input.strftime("%Y-%m-%d")  
    annee, mois, jour = date_str.split("-")  
    mois = str(int(mois))  
    jour = str(int(jour))

    if len(mois) == 1 and len(jour) == 1:
        date_formatee = f"{annee}- {mois}- {jour}"
    elif len(mois) == 1:
        date_formatee = f"{annee}- {mois}-{jour}"
    elif len(jour) == 1:
        date_formatee = f"{annee}-{mois}- {jour}"
    else:
        date_formatee = f"{annee}-{mois}-{jour}"
    return date_formatee

# Fonction pour récupérer le nombre de pièces conformes (OK)
def get_nombre_pieces_ok(date_production):
    date_production_formatee = format_date(date_production)
    date_debut = f"{date_production_formatee} 06:00:00"
    date_fin = f"{date_production_formatee} 22:00:00"

    conn = pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="bb02",
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with conn.cursor() as cursor:
            query = """
                SELECT COUNT(*) AS nombre_pieces_ok 
                FROM opb500 
                WHERE ETAT_OPB500 = 'OK' 
                AND Fin_OPB500 >= %s 
                AND Fin_OPB500 < %s;
            """
            cursor.execute(query, (date_debut, date_fin))
            result = cursor.fetchone()
            return result["nombre_pieces_ok"]
    finally:
        conn.close()

# Fonction pour récupérer le nombre de pièces non conformes (NOK) et leurs références
def get_pieces_nok_data(date_production):
    date_production_formatee = format_date(date_production)
    date_debut = f"{date_production_formatee} 06:00:00"
    date_fin = f"{date_production_formatee} 22:00:00"

    conn = pymysql.connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="bb02",
        port=3306,
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with conn.cursor() as cursor:
            query = """
                SELECT 
                    COUNT(CASE 
                        WHEN (
                            spp.ETAT_OPB10 = 'NOK' OR 
                            spp.ETAT_OPB20 = 'NOK' OR 
                            spp.ETAT_OPB80 = 'NOK' OR 
                            spp.ETAT_OPB90 = 'NOK' OR 
                            spp.ETAT_OPB100 = 'NOK' OR 
                            spp.ETAT_OPB150 = 'NOK' OR 
                            spp.ETAT_OPB200 = 'NOK' OR 
                            spp.ETAT_OPB300 = 'NOK' OR 
                            spp.ETAT_OPB400 = 'NOK' OR 
                            spp.ETAT_OPB450 = 'NOK' OR
                            spp.ETAT_OPB500 = 'ATT'
                        ) AND (
                            (o10.Debut_OPB10 >= %s AND o10.Debut_OPB10 <= %s) 
                            OR 
                            (o500.Fin_OPB500 >= %s AND o500.Fin_OPB500 <= %s)
                        )
                        THEN 1 
                    END) AS nombre_pieces_nok,
                    
                    GROUP_CONCAT(DISTINCT CASE 
                        WHEN (
                            spp.ETAT_OPB10 = 'NOK' OR 
                            spp.ETAT_OPB20 = 'NOK' OR 
                            spp.ETAT_OPB80 = 'NOK' OR 
                            spp.ETAT_OPB90 = 'NOK' OR 
                            spp.ETAT_OPB100 = 'NOK' OR 
                            spp.ETAT_OPB150 = 'NOK' OR 
                            spp.ETAT_OPB200 = 'NOK' OR 
                            spp.ETAT_OPB300 = 'NOK' OR 
                            spp.ETAT_OPB400 = 'NOK' OR 
                            spp.ETAT_OPB450 = 'NOK' OR
                            spp.ETAT_OPB500 = 'ATT'
                        ) 
                        THEN spp.Numero_Busbar 
                    END SEPARATOR '; ') AS busbars_non_conformes
                FROM 
                    suivi_produit_process spp
                JOIN 
                    opb10 o10
                ON 
                    spp.Numero_Busbar COLLATE utf8_general_ci = o10.Busbar COLLATE utf8_general_ci
                LEFT JOIN 
                    opb500 o500
                ON 
                    spp.Numero_Busbar COLLATE utf8_general_ci = o500.Busbar COLLATE utf8_general_ci
                WHERE 
                    (o10.Debut_OPB10 >= %s AND o10.Debut_OPB10 <= %s)
                    OR 
                    (o500.Fin_OPB500 >= %s AND o500.Fin_OPB500 <= %s);
            """
            cursor.execute(query, (date_debut, date_fin, date_debut, date_fin, date_debut, date_fin, date_debut, date_fin))
            result = cursor.fetchone()
            return result["nombre_pieces_nok"], result["busbars_non_conformes"]
    finally:
        conn.close()

# Interface Streamlit
st.markdown("<h1 style='text-align: center; color: #000000;'>Mersen EV</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center; color: #707070;'>Statistiques de la chaîne de production BB02</h2>", unsafe_allow_html=True)

# Sélection de la date
date_selection = st.date_input("📅 Sélectionne une date")
# Récupérer les données des pièces conformes et non conformes
nombre_pieces_ok = get_nombre_pieces_ok(date_selection)
nombre_pieces_nok, busbars_non_conformes = get_pieces_nok_data(date_selection)

# Calcul du pourcentage des pièces conformes
total_pieces = nombre_pieces_ok + nombre_pieces_nok
pourcentage_ok = (nombre_pieces_ok / total_pieces * 100) if total_pieces > 0 else "N/A"

# Affichage des pièces conformes
if nombre_pieces_ok > 0:
    st.success(f"✅ Nombre de pièces conformes trouvées : **{nombre_pieces_ok}**")
    st.info(f"📊 **Pourcentage de pièces conformes : {pourcentage_ok:.2f}%**" if pourcentage_ok != "N/A" else "📊 **Pourcentage de pièces conformes : N/A**")
else:
    st.warning("⚠️ Aucune pièce conforme trouvée pour cette période.")

# Affichage des pièces non conformes
if nombre_pieces_nok > 0:
    st.error(f"❌ Nombre de pièces non conformes trouvées : **{nombre_pieces_nok}**")

    # Affichage des références sous forme de tableau
    references_list = busbars_non_conformes.split("; ") if busbars_non_conformes else []
    df_references = pd.DataFrame(references_list, columns=["Référence Busbar non conforme"])
    st.dataframe(df_references)
    
else:
    st.success("✅ Aucune pièce non conforme trouvée pour cette période.")
