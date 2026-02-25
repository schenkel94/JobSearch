import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time as time_mod
import re

st.set_page_config(page_title="Job Hunter Pro", page_icon="🕵️", layout="wide")

# --- TRADUÇÃO PARA FONTES GRINGAS ---
TRADUCOES = {
    "Analista de Dados": "Data Analyst",
    "Engenheiro de Dados": "Data Engineer",
    "Cientista de Dados": "Data Scientist",
    "Desenvolvedor": "Developer"
}

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configurações de Busca")
    query_role = st.text_input("Cargo", "Analista de Dados")
    
    country_map = {"Brasil": "106057199", "Portugal": "100364837", "EUA": "103644278"}
    sel_country = st.selectbox("País", list(country_map.keys()))
    
    wt_map = {"Qualquer": "", "Remoto": "2", "Híbrido": "3", "Presencial": "1"}
    sel_wt = st.selectbox("Modalidade", list(wt_map.keys()))
    
    tpr_map = {"Qualquer": "", "24 Horas": "r86400", "Semana": "r604800", "Mês": "r2592000"}
    sel_tpr = st.selectbox("Período (LinkedIn)", list(tpr_map.keys()))
    
    max_p = st.slider("Páginas LinkedIn", 1, 15, 3)

# --- MOTORES DE BUSCA ---

def fetch_linkedin(role, geo, wt, tpr, pages):
    jobs = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    for p in range(pages):
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={role}&geoId={geo}&f_WT={wt}&f_TPR={tpr}&start={p*50}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for li in soup.select('li'):
                t = li.select_one('.base-search-card__title')
                c = li.select_one('.base-search-card__subtitle')
                l = li.select_one('a.base-card__full-link')
                loc = li.select_one('.job-search-card__location')
                
                if t and l:
                    loc_txt = loc.get_text(strip=True) if loc else ""
                    # Validação de país para evitar lixo do LinkedIn
                    if sel_country == "Brasil" and not any(x in loc_txt.lower() for x in ["brazil", "brasil", "remoto", "sp", "rj"]):
                        continue
                        
                    jobs.append({
                        "Cargo": t.get_text(strip=True),
                        "Empresa": c.get_text(strip=True) if c else "N/A",
                        "Origem": "LinkedIn",
                        "Link": l['href'].split('?')[0],
                        "Local": loc_txt
                    })
        except: break
    return jobs

def fetch_remotive(role):
    # Força busca em inglês para a Remotive
    search = TRADUCOES.get(role, role)
    try:
        r = requests.get(f"https://remotive.com/api/remote-jobs?search={search}", timeout=5)
        return [{"Cargo": j['title'], "Empresa": j['company_name'], "Origem": "Remotive", "Link": j['url'], "Local": "Remoto"} for j in r.json().get('jobs', [])]
    except: return []

def fetch_adzuna(role):
    # Adzuna API Pública (Simulada via endpoint público de busca rápida)
    search = TRADUCOES.get(role, role)
    # Nota: Adzuna real exige API KEY, mas podemos linkar a busca direta
    return [{
        "Cargo": f"{role} (Busca)", 
        "Empresa": "Múltiplas", 
        "Origem": "Adzuna", 
        "Link": f"https://www.adzuna.com.br/search?q={role}", 
        "Local": "Brasil"
    }]

def fetch_google_jobs(role):
    # O Google Jobs não tem API grátis, mas podemos gerar o link de busca "limpa" (bypass algoritmo)
    query = role.replace(" ", "+")
    link = f"https://www.google.com/search?q={query}&ibp=htl;jobs"
    return [{"Cargo": f"Ver no Google Jobs: {role}", "Empresa": "Várias", "Origem": "Google Jobs", "Link": link, "Local": "Global"}]

# --- EXECUÇÃO ---

st.header(f"🔍 Resultados para: {query_role}")

if st.button("🚀 EXECUTAR VARREDURA COMPLETA"):
    with st.spinner("Varrendo LinkedIn, Remotive, Adzuna e Google..."):
        
        # 1. LinkedIn
        li_data = fetch_linkedin(query_role, country_map[sel_country], wt_map[sel_wt], tpr_map[sel_tpr], max_p)
        
        # 2. Remotive
        re_data = fetch_remotive(query_role)
        
        # 3. Adzuna + Google (Links Estruturados)
        ad_data = fetch_adzuna(query_role)
        go_data = fetch_google_jobs(query_role)
        
        all_results = li_data + re_data + ad_data + go_data
        
        if all_results:
            df = pd.DataFrame(all_results).drop_duplicates(subset=['Link'])
            
            # Métrica de fontes
            c1, c2, c3 = st.columns(3)
            c1.metric("LinkedIn", len(li_data))
            c2.metric("Remotive", len(re_data))
            c3.metric("Outros", len(ad_data) + len(go_data))

            st.data_editor(
                df,
                column_config={
                    "Link": st.column_config.LinkColumn("Link", display_text="Acessar Vaga ↗️"),
                    "Origem": st.column_config.TextColumn("Fonte"),
                    "Local": st.column_config.TextColumn("Localização")
                },
                hide_index=True,
                use_container_width=True
            )
            
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Baixar Planilha CSV", csv, "vagas_consolidado.csv", "text/csv")
        else:
            st.warning("Nenhum resultado encontrado. Tente mudar o termo de busca.")
