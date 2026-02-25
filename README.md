# 🕵️ LinkedIn Job Hunter (Anti-Algoritmo)
* [Acesse o app no Streamlit]([https://www.python.org/](https://schenkeljobsearch.streamlit.app/))

Uma ferramenta web desenvolvida em Python para buscar vagas no LinkedIn de forma pura, utilizando o endpoint público da plataforma. O objetivo é permitir que o usuário encontre oportunidades reais baseadas em filtros técnicos, ignorando as recomendações enviesadas do algoritmo do LinkedIn.

## 🚀 Funcionalidades

* **Busca Direta**: Acesso ao endpoint `jobs-guest` do LinkedIn para resultados não manipulados.
* **Filtros Personalizados**: Configure cargo, localidade (via geoId), modalidade (Remoto/Híbrido) e período de publicação diretamente na interface.
* **Whitelist de Títulos**: Filtro inteligente via Regex que garante que apenas vagas com termos específicos no título apareçam na lista.
* **Interface Web Interativa**: Desenvolvido com Streamlit para uma experiência de usuário simples e eficiente.
* **Exportação**: Download dos resultados em formato CSV com um clique.
* **Links Diretos**: Botão dedicado para abrir a vaga em uma nova guia do navegador.

## 🛠️ Tecnologias Utilizadas

* [Python](https://www.python.org/)
* [Streamlit](https://streamlit.io/) (Interface Web)
* [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) (Web Scraping)
* [Pandas](https://pandas.pydata.org/) (Manipulação de Dados)
* [Requests](https://requests.readthedocs.io/) (HTTP)

## 📦 Como Instalar e Rodar

1. **Clone o repositório**:
   ```bash
   git clone [https://github.com/seu-usuario/linkedin-job-hunter.git](https://github.com/seu-usuario/linkedin-job-hunter.git)
   cd linkedin-job-hunter
