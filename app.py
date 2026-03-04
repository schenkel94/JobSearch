import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time as time_mod
import re

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="LinkedIn Job Hunter", page_icon="🕵️", layout="wide")

st.title("🕵️ LinkedIn Job Hunter (Anti-Algoritmo)")

# --- SIDEBAR: CONFIGURAÇÕES DA BUSCA ---
st.sidebar.header("Configurações da Busca")

query_role = st.sidebar.text_input("Cargo/Keywords", "Analista de Dados")

# Mapeamento exaustivo de geoIds conforme solicitado
geo_locations = {
    "Brasil (País)": "106057199",
    "América Latina": "91000007",
    "Estados Unidos": "103644278",
    "Portugal": "100364837",
    "Argentina": "100446943",
    "--- ESTADOS BRASILEIROS ---": "106057199",
    "Acre": "105555430", "Alagoas": "101650381", "Amapá": "101416467",
    "Amazonas": "103135063", "Bahia": "105740332", "Ceará": "101188310",
    "Distrito Federal": "100863923", "Espírito Santo": "104192087", "Goiás": "105459306",
    "Maranhão": "106292275", "Mato Grosso": "100236487", "Mato Grosso do Sul": "105943343",
    "Minas Gerais": "102830846", "Pará": "106602330", "Paraíba": "104278788",
    "Paraná": "100080645", "Pernambuco": "103185348", "Piauí": "103233866",
    "Rio de Janeiro": "102551460", "Rio Grande do Norte": "103063548", "Rio Grande do Sul": "105268305",
    "Rondônia": "102506634", "Roraima": "102717983", "Santa Catarina": "102872391",
    "São Paulo": "104815124", "Sergipe": "105572886", "Tocantins": "106191438"
}

selected_loc = st.sidebar.selectbox("Localidade", list(geo_locations.keys()), index=0)
geo_id = geo_locations[selected_loc]

# Modalidade
workplace_options = {"Remoto": "2", "Híbrido": "3", "Presencial": "1", "Qualquer": ""}
workplace_type = st.sidebar.selectbox("Modalidade", list(workplace_options.keys()), index=0)
f_wt_val = workplace_options[workplace_type]

# Período
time_options = {
    "Últimas 24h": "r86400", "Últimas 12h": "r43200", "Última Hora": "r3600",
    "Última Semana": "r604800", "Último Mês": "r2592000", "Qualquer Momento": ""
}
time_posted_range = st.sidebar.selectbox("Data de Publicação", list(time_options.keys()), index=0)
f_tpr_val = time_options[time_posted_range]

max_pages = st.sidebar.slider("Número de páginas", 1, 30, 15)
sleep_s = st.sidebar.slider("Intervalo (segundos)", 0.5, 5.0, 3.00)

# Whitelist
st.sidebar.subheader("Filtro de Relevância")
whitelist_input = st.sidebar.text_area("Termos obrigatórios:", "Analista de Dados\nData Analyst\nBusiness Intelligence\nBI")
title_whitelist_terms = [t.strip() for t in whitelist_input.split('\n') if t.strip()]

# --- LÓGICA ---
headers = {'User-Agent': 'Mozilla/5.0'}

def parse_job_cards(html, terms):
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('li')
    if not cards: return None
    
    rows = []
    for li in cards:
        title_el = li.select_one('h3.base-search-card__title')
        cargo = title_el.get_text(strip=True) if title_el else None
        
        if cargo and any(re.search(re.escape(t), cargo, re.I) for t in terms):
            time_el = li.select_one('time')
            rows.append({
                'Cargo': cargo,
                'Empresa': li.select_one('h4.base-search-card__subtitle').get_text(strip=True),
                'Publicada': time_el.get_text(strip=True) if time_el else "N/A",
                'Data_ISO': time_el.get('datetime') if time_el else "0000-00-00",
                'Link': li.select_one('a.base-card__full-link').get('href').split('?')[0]
            })
    return rows

if st.button("🚀 Iniciar Busca"):
    all_rows, seen_links = [], set()
    bar = st.progress(0)
    status = st.empty()

    for p in range(max_pages):
        status.text(f"Página {p+1}/{max_pages} | {len(all_rows)} vagas...")
        res = requests.get('https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search', 
                           params={'keywords': query_role, 'geoId': geo_id, 'f_WT': f_wt_val, 'f_TPR': f_tpr_val, 'start': p*25}, 
                           headers=headers)
        
        if res.status_code != 200: break
        
        found = parse_job_cards(res.text, title_whitelist_terms)
        if found is None: break
        
        for r in found:
            if r['Link'] not in seen_links:
                seen_links.add(r['Link'])
                all_rows.append(r)
        
        bar.progress((p + 1) / max_pages)
        time_mod.sleep(sleep_s)

    if all_rows:
        df = pd.DataFrame(all_rows).sort_values(by='Data_ISO', ascending=False).drop(columns=['Data_ISO'])
        st.data_editor(df, column_config={"Link": st.column_config.LinkColumn("Link", display_text="Abrir ↗️")}, hide_index=True)
        st.download_button("📥 Baixar CSV", df.to_csv(index=False).encode('utf-8-sig'), "vagas.csv", "text/csv")
    else:
        st.error("Nenhuma vaga encontrada.")
