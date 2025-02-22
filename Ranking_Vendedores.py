import pandas as pd
import mysql.connector
import decimal
import streamlit as st

def bd_phoenix(vw_name):

    config = {
    'user': 'user_automation_jpa',
    'password': 'luck_jpa_2024',
    'host': 'comeia.cixat7j68g0n.us-east-1.rds.amazonaws.com',
    'database': 'test_phoenix_maceio'
    }

    conexao = mysql.connector.connect(**config)

    cursor = conexao.cursor()

    request_name = f'SELECT * FROM {vw_name}'

    cursor.execute(request_name)

    resultado = cursor.fetchall()

    cabecalho = [desc[0] for desc in cursor.description]

    cursor.close()

    conexao.close()

    df = pd.DataFrame(resultado, columns=cabecalho)

    df = df.applymap(lambda x: float(x) if isinstance(x, decimal.Decimal) else x)

    return df

def definir_html(df_ref):

    html=df_ref.to_html(index=False)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                text-align: center;  /* Centraliza o texto */
            }}
            table {{
                margin: 0 auto;  /* Centraliza a tabela */
                border-collapse: collapse;  /* Remove espaço entre as bordas da tabela */
            }}
            th, td {{
                padding: 8px;  /* Adiciona espaço ao redor do texto nas células */
                border: 1px solid black;  /* Adiciona bordas às células */
                text-align: center;
            }}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """

    return html

def criar_output_html(nome_html, html, titulo_inclusos, titulo_vendas, titulo_total, titulo_cld, titulo_total_s_cld, servico):

    with open(nome_html, "w", encoding="utf-8") as file:

        file.write(f'<p style="font-size:30px;">{servico}</p>\n\n')

        file.write(f'<p style="font-size:25px;">{titulo_inclusos}</p>\n\n')

        file.write(f'<p style="font-size:25px;">{titulo_vendas}</p>\n\n')

        file.write(f'<p style="font-size:25px;">{titulo_total}</p>\n\n')

        file.write(f'<p style="font-size:25px;">{titulo_cld}</p>\n\n')

        file.write(f'<p style="font-size:25px;">{titulo_total_s_cld}</p>\n\n')
        
        file.write(html)

def gerar_df_data_filtrado(data_inicial, data_final):

    df_data_filtrado = st.session_state.df_ranking_vendedores[(st.session_state.df_ranking_vendedores['Data_Execucao'] >= data_inicial) & 
                                                                (st.session_state.df_ranking_vendedores['Data_Execucao'] <= data_final)].reset_index(drop=True)
    
    df_data_filtrado['Total ADT | CHD'] = df_data_filtrado['Total_ADT'] + df_data_filtrado['Total_CHD']

    return df_data_filtrado

def gerar_df_servico_selecionado(df_data_filtrado, servico):

    df_servico_selecionado = df_data_filtrado[df_data_filtrado['Servico'].isin(servico)].reset_index(drop=True)

    df_servico_selecionado['Reserva_Mae'] = df_servico_selecionado['Reserva'].str[:10]

    st.session_state.df_guias_in['Reserva_Mae'] = st.session_state.df_guias_in['Reserva'].str[:10]
    
    df_servico_selecionado = pd.merge(df_servico_selecionado, st.session_state.df_guias_in[['Reserva_Mae', 'Guia']], on='Reserva_Mae', how='left')

    df_servico_selecionado['CLD'] = df_servico_selecionado['Observacao'].apply(lambda x: 'X' if 'CLD' in x.upper() else '')

    return df_servico_selecionado

def gerar_df_ranking(df_servico_selecionado, servico):

    df_ranking = df_servico_selecionado.groupby('Vendedor', as_index=False)['Total ADT | CHD'].sum()
    
    df_inclusos_guia = df_servico_selecionado.groupby('Guia', as_index=False)['Total ADT | CHD'].sum()
    
    df_inclusos_guia = df_inclusos_guia.rename(columns={'Guia': 'Vendedor', 'Total ADT | CHD': 'Paxs Inclusos'})

    df_ranking = pd.merge(df_ranking, df_inclusos_guia, on='Vendedor', how='left')

    df_ranking['Paxs Inclusos'] = df_ranking['Paxs Inclusos'].fillna(0)

    df_ranking['Paxs Totais'] = df_ranking['Paxs Inclusos'] + df_ranking['Total ADT | CHD']

    df_ranking = df_ranking.sort_values(by='Paxs Totais', ascending=False)

    df_ranking = df_ranking.rename(columns={'Total ADT | CHD': 'Paxs Opcionais'})  

    for coluna in ['Paxs Opcionais', 'Paxs Inclusos', 'Paxs Totais']:

        df_ranking[coluna] = df_ranking[coluna].astype(int)

    return df_ranking

def plotar_titulo(df_ranking, df_servico_selecionado, servico, container_2):
    
    total_paxs = df_servico_selecionado['Total ADT | CHD'].sum()

    total_paxs_vendedores = df_ranking['Paxs Opcionais'].sum()

    total_cld = df_servico_selecionado[df_servico_selecionado['CLD']=='X']['Total ADT | CHD'].sum()

    st.session_state.titulo_inclusos = f'Incluso = {int(total_paxs-total_paxs_vendedores)}'

    st.session_state.titulo_vendas = f'Vendas = {int(total_paxs_vendedores)}'

    st.session_state.titulo_total = f'Total = {int(total_paxs)}'

    st.session_state.titulo_cld = f'CLD = {int(total_cld)}'

    st.session_state.titulo_total_s_cld = f'Total sem CLD = {int(total_paxs-total_cld)}'

    st.session_state.servico = f"Serviços: {' + '.join(servico)}"

    container_2.write(st.session_state.servico)
    
    container_2.write(st.session_state.titulo_inclusos)

    container_2.write(st.session_state.titulo_vendas)

    container_2.write(st.session_state.titulo_total)

    container_2.write(st.session_state.titulo_cld)
    
    container_2.write(st.session_state.titulo_total_s_cld)

def gerar_html_content(df):

    html = definir_html(df)

    criar_output_html(st.session_state.nome_html, html, st.session_state.titulo_inclusos, st.session_state.titulo_vendas, 
                        st.session_state.titulo_total, st.session_state.titulo_cld, st.session_state.titulo_total_s_cld, 
                        st.session_state.servico)
    
    with open(st.session_state.nome_html, "r", encoding="utf-8") as file:

        html_content = file.read()

    return html_content

def plotar_botao_download(row3, html_content, html_content_2):

    with row3[0]:

        st.download_button(
            label="Baixar Arquivo HTML",
            data=html_content,
            file_name=st.session_state.nome_html,
            mime="text/html"
        )

    with row3[1]:

        st.download_button(
            label="Baixar Arquivo HTML | Alejandro",
            data=html_content_2,
            file_name=st.session_state.nome_html_2,
            mime="text/html"
        )

st.set_page_config(layout='wide')

if not 'df_ranking_vendedores' in st.session_state:

    with st.spinner('Puxando dados do phoenix...'):

        st.session_state.df_guias_in = bd_phoenix('vw_guia_reserva_in')

        st.session_state.df_ranking_vendedores = bd_phoenix('vw_ranking_vendedores')

st.title('Ranking Vendedores')

st.divider()

senha = st.text_input('Digite a senha')

if senha=='luckmcz@1960':

    row0 = st.columns(2)
    
    with row0[1]:
    
        container_dados = st.container()
    
        atualizar_dados = container_dados.button('Carregar Dados do Phoenix', use_container_width=True)
    
    if atualizar_dados:
    
        with st.spinner('Puxando dados do phoenix...'):

            st.session_state.df_guias_in = bd_phoenix('vw_guia_reserva_in')

            st.session_state.df_ranking_vendedores = bd_phoenix('vw_ranking_vendedores')
    
    with row0[0]:
    
        data_inicial = st.date_input('Data Inicial', value=None ,format='DD/MM/YYYY', key='data_inicial')
    
        data_final = st.date_input('Data Final', value=None ,format='DD/MM/YYYY', key='data_final')
    
    if data_inicial and data_final:

        df_data_filtrado = gerar_df_data_filtrado(data_inicial, data_final)
    
        with row0[1]:
    
            container_passeios = st.container(border=True)
    
            servico = container_passeios.multiselect('Passeios', sorted(df_data_filtrado['Servico'].unique().tolist()), default=None)
    
        st.divider()
    
        row2 = st.columns(1)
    
        container_2 = st.container(border=True)
    
        if len(servico)>0:

            df_servico_selecionado = gerar_df_servico_selecionado(df_data_filtrado, servico)

            df_ranking = gerar_df_ranking(df_servico_selecionado, servico)

            plotar_titulo(df_ranking, df_servico_selecionado, servico, container_2)
    
            container_2.dataframe(df_ranking, hide_index=True, use_container_width=True)
    
            st.session_state.df_ranking = df_ranking
    
            st.session_state.nome_html = f"{servico[0].split(' ')[0]}.html"
    
            st.session_state.nome_html_2 = f"Alejandro | {servico[0].split(' ')[0]}.html"
    
    if 'df_ranking' in st.session_state and len(servico)>0:

        html_content = gerar_html_content(st.session_state.df_ranking)

        html_content_2 = gerar_html_content(st.session_state.df_ranking[['Vendedor', 'Paxs Opcionais']])
    
        row3 = st.columns(2)

        plotar_botao_download(row3, html_content, html_content_2)
