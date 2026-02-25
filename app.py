import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time as time_mod
import re

st.set_page_config(page_title="Job Hunter v3", page_icon="⚡", layout="wide")

# --- DICIONÁRIO DE TRADUÇÃO SIMPLES (Para aumentar alcance) ---
TRADUCOES = {
    "Analista de Dados": "Data Analyst",
    "Engenheiro de Dados": "Data Engineer",
    "Cientista de Dados": "Data Scientist",
    "Desenvolvedor": "Developer",
    "Gerente de Projetos": "Project Manager"
}

st.title("⚡ Job Hunter Ultra (Fixed & Multi-Source)")

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 Configurações")
    query_role = st.text_input("Cargo", "Analista de Dados")
    
    # Checkbox para tradução
    use_english = st.checkbox("Buscar também termo em Inglês", value=True)
    
    location_map = {"Brasil": "106057199", "Portugal": "100364837", "EUA": "103644278", "Global": ""}
    sel_country = st.selectbox("País", list(location_map.keys()))
    
    wt_map = {"Qualquer": "", "Remoto": "2", "Híbrido": "3", "Presencial": "1"}
    sel_wt = st.selectbox("Modalidade", list(wt_map.keys()))
    
    max_p = st.slider("Páginas LinkedIn", 1, 15, 3)

# --- MOTORES DE BUSCA ---

def get_remotive(role):
    # Remotive funciona melhor com termos em inglês
    search_term = TRADUCOES.get(role, role) if use_english else role
    try:
        url = f"https://remotive.com/api/remote-jobs?search={search_term}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return [{"Cargo": j['title'], "Empresa": j['company_name'], "Origem": "Remotive", "Link": j['url'], "Loc": "Remoto"} for j in data.get('jobs', [])]
    except: return []
    return []

def get_linkedin(role, geo_id, wt, pages):
    jobs = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0'}
    for p in range(pages):
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={role}&geoId={geo_id}&f_WT={wt}&start={p*50}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            cards = soup.select('li')
            for c in cards:
                t = c.select_one('.base-search-card__title')
                comp = c.select_one('.base-search-card__subtitle')
                lk = c.select_one('a.base-card__full-link')
                loc = c.select_one('.job-search-card__location')
                
                if t and lk:
                    loc_txt = loc.get_text(strip=True) if loc else ""
                    # FILTRO DE SEGURANÇA: Se escolheu Brasil, ignora se a localização não contiver Brasil ou estados brasileiros
                    if sel_country == "Brasil" and not any(x in loc_txt.lower() for x in ["brasil", "brazil", "são paulo", "rio de", "minas", "remoto"]):
                        continue
                        
                    jobs.append({
                        "Cargo": t.get_text(strip=True),
                        "Empresa": comp.get_text(strip=True) if comp else "N/A",
                        "Origem": "LinkedIn",
                        "Link": lk['href'].split('?')[0],
                        "Loc": loc_txt
                    })
        except: break
    return jobs

# --- EXECUÇÃO ---
if st.button("🚀 BUSCAR EM TODAS AS FONTES"):
    all_results = []
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.status("Buscando no LinkedIn..."):
            li_results = get_linkedin(query_role, location_map[sel_country], wt_map[sel_wt], max_p)
            all_results.extend(li_results)
            st.write(f"{len(li_results)} vagas encontradas.")

    with col2:
        with st.status("Buscando na Remotive..."):
            re_results = get_remotive(query_role)
            all_results.extend(re_results)
            st.write(f"{len(re_results)} vagas encontradas.")

    if all_results:
        df = pd.DataFrame(all_results).drop_duplicates(subset=['Link'])
        
        # Filtro final de Whitelist (aplicado sobre tudo)
        st.subheader(f"📊 Resultados Consolidados ({len(df)} vagas)")
        
        st.data_editor(
            df,
            column_config={
                "Link": st.column_config.LinkColumn("Link", display_text="Ver Vaga ↗️"),
                "Loc": "Localização Original"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.error("Nenhum resultado em nenhuma fonte. Tente termos mais genéricos.")
