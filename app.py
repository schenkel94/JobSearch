import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time as time_mod
import re

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Ultimate Job Hunter", page_icon="🚀", layout="wide")

st.title("🚀 Ultimate Job Hunter: LinkedIn + Remotive")
st.markdown("Fugindo do algoritmo e centralizando vagas de múltiplas fontes.")

# --- SIDEBAR: CONFIGURAÇÕES ---
st.sidebar.header("🔍 Filtros de Busca")
query_role = st.sidebar.text_input("Cargo desejado", "Data Analyst")

with st.sidebar.expander("Configurações LinkedIn"):
    location_options = {"Brasil": "106057199", "Portugal": "100364837", "EUA": "103644278", "Global": ""}
    selected_loc = st.selectbox("Localidade", list(location_options.keys()))
    geo_id = location_options[selected_loc]
    max_pages = st.slider("Páginas LinkedIn", 1, 20, 5)

st.sidebar.subheader("🎯 Filtro de Títulos")
whitelist_input = st.sidebar.text_area(
    "Termos obrigatórios (um por linha):",
    "analista de dados\ndata analyst\ndata science\nanalytics",
    height=120
)
whitelist_terms = [t.strip() for t in whitelist_input.split('\n') if t.strip()]

# --- LÓGICA DE FILTRAGEM ---
def passes_filter(title, terms):
    if not title or not terms: return True
    regex = re.compile('(' + '|'.join([re.escape(t) for t in terms]) + ')', flags=re.IGNORECASE)
    return regex.search(str(title)) is not None

# --- SCRAPER 1: LINKEDIN ---
def fetch_linkedin(role, geo, pages, terms):
    jobs = []
    base_url = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    for i in range(pages):
        params = {'keywords': role, 'geoId': geo, 'start': i * 50}
        try:
            res = requests.get(base_url, params=params, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for li in soup.select('li'):
                title = li.select_one('.base-search-card__title').get_text(strip=True) if li.select_one('.base-search-card__title') else ""
                if passes_filter(title, terms):
                    company = li.select_one('.base-search-card__subtitle').get_text(strip=True) if li.select_one('.base-search-card__subtitle') else "N/A"
                    link = li.select_one('a.base-card__full-link')['href'].split('?')[0]
                    jobs.append({"Cargo": title, "Empresa": company, "Origem": "LinkedIn", "Link": link})
            time_mod.sleep(1)
        except: break
    return jobs

# --- SCRAPER 2: REMOTIVE (API) ---
def fetch_remotive(role, terms):
    jobs = []
    # Remotive tem uma API pública que não exige login
    api_url = f"https://remotive.com/api/remote-jobs?search={role}"
    try:
        res = requests.get(api_url, timeout=10)
        data = res.json()
        for job in data.get('jobs', []):
            if passes_filter(job['title'], terms):
                jobs.append({
                    "Cargo": job['title'],
                    "Empresa": job['company_name'],
                    "Origem": "Remotive",
                    "Link": job['url']
                })
    except: pass
    return jobs

# --- EXECUÇÃO ---
if st.button("🔥 BUSCAR VAGAS AGORA"):
    with st.spinner("Varrendo a internet..."):
        # Rodando as buscas
        results_li = fetch_linkedin(query_role, geo_id, max_pages, whitelist_terms)
        results_re = fetch_remotive(query_role, whitelist_terms)
        
        all_jobs = results_li + results_re
        
        if all_jobs:
            df = pd.DataFrame(all_jobs)
            
            st.success(f"Encontramos {len(df)} vagas!")
            
            # Configuração da Tabela com Link clicável (botão virtual)
            st.data_editor(
                df,
                column_config={
                    "Link": st.column_config.LinkColumn(
                        "Link da Vaga",
                        help="Clique para abrir a vaga em uma nova guia",
                        validate=r"^https://.*",
                        display_text="Abrir Vaga ↗️" # Transforma o link em um "botão" de texto
                    ),
                    "Origem": st.column_config.TextColumn(
                        "Fonte",
                        help="De onde essa vaga foi extraída"
                    )
                },
                hide_index=True,
                use_container_width=True,
                disabled=True # Deixa a tabela apenas para visualização
            )
            
            # Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Planilha", csv, "vagas.csv", "text/csv")
        else:
            st.error("Nenhuma vaga encontrada. Tente ajustar os termos ou o cargo.")
