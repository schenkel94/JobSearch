import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time as time_mod
import re

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Job Hunter Ultra", page_icon="🎯", layout="wide")

st.title("🎯 Job Hunter Ultra: Multi-Source")
st.markdown("Busca agregada em LinkedIn, Remotive, The Muse e Working Nomads.")

# --- SIDEBAR: FILTROS TÉCNICOS ---
st.sidebar.header("🔍 Configurações Globais")
query_role = st.sidebar.text_input("Cargo (Ex: Data Analyst)", "Analista de Dados")

# Filtros de Precisão (Exclusivos para fontes que suportam, como LinkedIn)
with st.sidebar.expander("Filtros de Refinamento (LinkedIn)", expanded=True):
    workplace_options = {"Qualquer": "", "Remoto": "2", "Híbrido": "3", "Presencial": "1"}
    workplace_type = st.selectbox("Modalidade", list(workplace_options.keys()))
    
    time_options = {"Qualquer Momento": "", "Últimas 24h": "r86400", "Última Semana": "r604800", "Último Mês": "r2592000"}
    time_posted = st.selectbox("Data de Publicação", list(time_options.keys()))
    
    location_options = {"Brasil": "106057199", "Portugal": "100364837", "EUA": "103644278", "Global": ""}
    geo_id = st.selectbox("País", list(location_options.keys()))
    max_pages = st.slider("Páginas LinkedIn", 1, 20, 5)

st.sidebar.subheader("🎯 Filtro de Títulos (Whitelist)")
whitelist_input = st.sidebar.text_area(
    "Só mostrar se o título contiver:",
    "analista de dados\ndata analyst\ndata science\nanalytics\nbi analyst",
    height=120
)
whitelist_terms = [t.strip() for t in whitelist_input.split('\n') if t.strip()]

# --- LÓGICA DE FILTRAGEM ---
def passes_filter(title, terms):
    if not title or not terms: return True
    regex = re.compile('(' + '|'.join([re.escape(t) for t in terms]) + ')', flags=re.IGNORECASE)
    return regex.search(str(title)) is not None

# --- FONTES DE BUSCA ---

def fetch_linkedin(role, geo, pages, wt, tpr, terms):
    jobs = []
    base_url = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for i in range(pages):
        params = {'keywords': role, 'geoId': geo, 'f_WT': wt, 'f_TPR': tpr, 'start': i * 50}
        try:
            res = requests.get(base_url, params=params, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for li in soup.select('li'):
                title_el = li.select_one('.base-search-card__title')
                if title_el:
                    title = title_el.get_text(strip=True)
                    if passes_filter(title, terms):
                        company = li.select_one('.base-search-card__subtitle').get_text(strip=True) if li.select_one('.base-search-card__subtitle') else "N/A"
                        link = li.select_one('a.base-card__full-link')['href'].split('?')[0]
                        jobs.append({"Cargo": title, "Empresa": company, "Origem": "LinkedIn", "Link": link})
            time_mod.sleep(0.5)
        except: break
    return jobs

def fetch_remotive(role, terms):
    jobs = []
    try:
        # Busca mais ampla para garantir resultados
        res = requests.get(f"https://remotive.com/api/remote-jobs?search={role}", timeout=10)
        data = res.json()
        for job in data.get('jobs', []):
            if passes_filter(job['title'], terms):
                jobs.append({"Cargo": job['title'], "Empresa": job['company_name'], "Origem": "Remotive", "Link": job['url']})
    except: pass
    return jobs

def fetch_themuse(role, terms):
    jobs = []
    try:
        # The Muse API
        res = requests.get(f"https://www.themuse.com/api/public/jobs?category=Data%20Science&page=1", timeout=10)
        data = res.json()
        for job in data.get('results', []):
            if passes_filter(job['name'], terms):
                jobs.append({"Cargo": job['name'], "Empresa": job['company']['name'], "Origem": "The Muse", "Link": job['refs']['landing_page']})
    except: pass
    return jobs

# --- EXECUÇÃO ---
if st.button("🔥 INICIAR VARREDURA MULTI-FONTE"):
    with st.spinner("Consultando bases de dados..."):
        
        # Coleta em paralelo (simulada)
        results = []
        results += fetch_linkedin(query_role, geo_id, max_pages, workplace_options[workplace_type], time_options[time_posted], whitelist_terms)
        results += fetch_remotive(query_role, whitelist_terms)
        results += fetch_themuse(query_role, whitelist_terms)
        
        if results:
            df = pd.DataFrame(results).drop_duplicates(subset=['Link'])
            
            st.success(f"Sucesso! {len(df)} vagas encontradas filtrando por {len(whitelist_terms)} termos.")
            
            # Tabela Interativa
            st.data_editor(
                df,
                column_config={
                    "Link": st.column_config.LinkColumn("Candidatar-se", display_text="Abrir Vaga ↗️"),
                    "Origem": st.column_config.TextColumn("Fonte"),
                    "Empresa": st.column_config.TextColumn("Empresa"),
                    "Cargo": st.column_config.TextColumn("Título da Vaga")
                },
                hide_index=True,
                use_container_width=True,
                disabled=True
            )
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar CSV", csv, "vagas_hunter.csv", "text/csv")
        else:
            st.error("Nenhuma vaga encontrada. Tente reduzir os termos da Whitelist ou mudar o cargo.")
