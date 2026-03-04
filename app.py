import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time as time_mod
import re
from io import BytesIO

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="LinkedIn Job Hunter", page_icon="🕵️", layout="wide")

st.title("🕵️ LinkedIn Job Hunter (Anti-Algoritmo)")
st.markdown("""
Esta ferramenta utiliza o endpoint público do LinkedIn para buscar vagas sem a interferência dos algoritmos de recomendação.
""")

# --- SIDEBAR: CONFIGURAÇÕES DA BUSCA ---
st.sidebar.header("Configurações da Busca")

query_role = st.sidebar.text_input("Cargo/Keywords", "Analista de Dados")
location_input = st.sidebar.text_input("Localidade", "Brasil")

# Tipo de vaga (f_WT)
workplace_options = {
    "Remoto": "2",
    "Híbrido": "3",
    "Presencial": "1",
    "Qualquer": ""
}
workplace_type = st.sidebar.selectbox("Modalidade", list(workplace_options.keys()), index=0)
f_wt_val = workplace_options[workplace_type]

# Período (f_TPR)
time_options = {
    "Última Hora": "r3600",
    "Últimas 12h": "r43200",
    "Últimas 24h": "r86400",
    "Última Semana": "r604800",
    "Último Mês": "r2592000",
    "Qualquer Momento": ""
}
time_posted_range = st.sidebar.selectbox("Data de Publicação", list(time_options.keys()), index=2)
f_tpr_val = time_options[time_posted_range]

max_pages = st.sidebar.slider("Número de páginas para ler", 1, 30, 15)
sleep_s = st.sidebar.slider("Intervalo entre páginas (segundos)", 0.5, 5.0, 3.00)

# --- FILTRO DE RELEVÂNCIA (WHITELIST) ---
st.sidebar.subheader("Filtro de Relevância")
whitelist_input = st.sidebar.text_area(
    "Termos obrigatórios no título (um por linha):",
    "Analista de Dados\nData Analyst\nBusiness Intelligence\nBI",
    height=150
)
title_whitelist_terms = [t.strip() for t in whitelist_input.split('\n') if t.strip()]

# --- LÓGICA DO SCRAPER ---

headers_obj = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def title_matches(title_txt, terms):
    if not title_txt or not terms:
        return False
    regex = re.compile('(' + '|'.join([re.escape(t) for t in terms]) + ')', flags=re.IGNORECASE)
    return regex.search(str(title_txt).strip()) is not None

def parse_job_cards(html_txt, terms):
    soup_obj = BeautifulSoup(html_txt, 'html.parser')
    # BUSCA INICIAL: Verifica se existem 'li' (cards de vaga) na página
    job_lis = soup_obj.select('li')
    
    if not job_lis:
        return None # Sinaliza que a página está realmente vazia

    rows_list = []
    for li_obj in job_lis:
        title_el = li_obj.select_one('h3.base-search-card__title')
        company_el = li_obj.select_one('h4.base-search-card__subtitle')
        time_el = li_obj.select_one('time')
        link_el = li_obj.select_one('a.base-card__full-link')

        cargo_val = title_el.get_text(strip=True) if title_el else None
        
        # Filtro de Whitelist
        if not title_matches(cargo_val, terms):
            continue

        empresa_val = company_el.get_text(strip=True) if company_el else None
        publicada_val = time_el.get_text(strip=True) if time_el else None
        link_val = link_el.get('href').split('?')[0] if link_el else None

        if cargo_val:
            rows_list.append({
                'Cargo': cargo_val,
                'Empresa': empresa_val,
                'Publicada em': publicada_val,
                'Link': link_val
            })
    return rows_list

# --- EXECUÇÃO ---
if st.button("🚀 Iniciar Busca"):
    all_rows = []
    seen_links = set()
    page_size = 25 
    base_url = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    for page_idx in range(max_pages):
        start_idx = page_idx * page_size
        status_text.text(f"Buscando página {page_idx + 1}... (Total acumulado: {len(all_rows)} vagas)")
        
        params_obj = {
            'keywords': query_role,
            'location': location_input,
            'f_WT': f_wt_val,
            'f_TPR': f_tpr_val,
            'start': start_idx
        }
        
        try:
            resp = requests.get(base_url, params=params_obj, headers=headers_obj, timeout=30)
            
            if resp.status_code != 200:
                st.warning(f"Busca encerrada: LinkedIn parou de responder (Status {resp.status_code}).")
                break
            
            # Chama a função otimizada
            rows = parse_job_cards(resp.text, title_whitelist_terms)
            
            # OTIMIZAÇÃO: Se 'rows' for None, a página não tinha nenhuma vaga.
            if rows is None:
                st.info(f"Fim dos resultados atingido na página {page_idx + 1}.")
                break
                
            for r in rows:
                if r['Link'] not in seen_links:
                    seen_links.add(r['Link'])
                    all_rows.append(r)
            
            progress_bar.progress((page_idx + 1) / max_pages)
            time_mod.sleep(sleep_s)
            
        except Exception as e:
            st.error(f"Erro na requisição: {e}")
            break

    status_text.text("Busca finalizada!")
    progress_bar.progress(1.0)
    
    if all_rows:
        df = pd.DataFrame(all_rows)
        st.success(f"Encontradas {len(df)} vagas relevantes!")
        
        st.data_editor(
            df,
            column_config={
                "Link": st.column_config.LinkColumn("Link Direto", display_text="Abrir Vaga ↗️"),
            },
            hide_index=True,
            use_container_width=True,
            disabled=True
        )
        
        csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(
            label="📥 Baixar Resultados como CSV",
            data=csv,
            file_name=f"vagas_{query_role.replace(' ', '_')}.csv",
            mime="text/csv",
        )
    else:
        st.error("Nenhuma vaga encontrada com os filtros de título aplicados.")
