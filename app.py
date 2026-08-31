import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Configuração da Página
st.set_page_config(page_title="Compras 360", layout="wide", page_icon="📊")
st.markdown(
    """
    <style>
    /* Esconde o ícone de 'olho' nativo do navegador (Edge/Chrome) para não duplicar com o do Streamlit */
    input[type="password"]::-ms-reveal,
    input[type="password"]::-ms-clear {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Identidade Visual
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
else:
    st.sidebar.markdown("<h2 style='text-align: center; color: #10B981;'>🏢 GREE ELECTRIC</h2>", unsafe_allow_html=True)
    st.sidebar.caption("<p style='text-align: center;'>Coloque uma imagem chamada 'logo.png' na pasta para substituí-la.</p>", unsafe_allow_html=True)

# Segurança
st.sidebar.title("🔒 Acesso Restrito")
senha_digitada = st.sidebar.text_input("Digite a senha da gerência:", type="password")

SENHA_CORRETA = "Gree2026"

if senha_digitada != SENHA_CORRETA:
    st.warning("⚠️ Bem-vindo ao portal Compras 360. Por favor, insira a senha no menu lateral para acessar os dados da operação.")
    st.stop()

st.sidebar.success("Acesso Liberado!")
st.sidebar.divider()

# Atualização de Dados (Upload)
st.sidebar.title("📂 Atualizar Base")
arquivo_upload = st.sidebar.file_uploader("Arraste a nova planilha aqui:", type=["xlsx"])

@st.cache_data
def carregar_dados(arquivo):
    if arquivo is not None:
        df = pd.read_excel(arquivo, sheet_name="Dados")
    else:
        df = pd.read_excel("COMPRADOR.xlsx", sheet_name="Dados")
        
    df['SAVING COMPRADOR'] = pd.to_numeric(df['SAVING COMPRADOR'], errors='coerce').fillna(0)
    df['Nº PEDIDO'] = df['Nº PEDIDO'].astype(str)
    
    if 'ANO' in df.columns:
        df['ANO'] = df['ANO'].fillna(0).astype(int).astype(str)
        df['ANO'] = df['ANO'].replace('0', 'Não Informado')
        
    if 'STATUS PRAZO' in df.columns:
        df['STATUS PRAZO'] = df['STATUS PRAZO'].astype(str).str.strip()
        
        def classificar_prazo(status):
            status_upper = status.upper()
            if "FINALIZADO" in status_upper:
                return "Finalizado"
            elif "CANCELADO" in status_upper:
                return "Cancelado"
            elif "ATRASO" in status_upper:
                return "Atrasado"
            elif "VENCER" in status_upper or "HOJE" in status_upper:
                return "No Prazo"
            else:
                return "Outros"
                
        df['CATEGORIA_PRAZO'] = df['STATUS PRAZO'].apply(classificar_prazo)
        
    return df

df = carregar_dados(arquivo_upload)

# Configurando as opções únicas para os filtros
anos_unicos = sorted(df['ANO'].dropna().unique().tolist(), reverse=True)
meses_unicos = df['MÊS REFERENTE'].dropna().unique().tolist()
compradores_unicos = df['COMPRADOR'].dropna().unique().tolist()
setores_unicos = df['SETOR'].dropna().unique().tolist() if 'SETOR' in df.columns else []
status_unicos = df['CATEGORIA_PRAZO'].dropna().unique().tolist() if 'CATEGORIA_PRAZO' in df.columns else []

# Memória do sistema: agora os filtros começam vazios por padrão
if 'filtro_ano' not in st.session_state: st.session_state['filtro_ano'] = []
if 'filtro_mes' not in st.session_state: st.session_state['filtro_mes'] = []
if 'filtro_comprador' not in st.session_state: st.session_state['filtro_comprador'] = []
if 'filtro_setor' not in st.session_state: st.session_state['filtro_setor'] = []
if 'filtro_status' not in st.session_state: st.session_state['filtro_status'] = []

st.sidebar.divider()
st.sidebar.title("Filtros da Operação")

if st.sidebar.button("Limpar Todos os Filtros"):
    st.session_state['filtro_ano'] = []
    st.session_state['filtro_mes'] = []
    st.session_state['filtro_comprador'] = []
    st.session_state['filtro_setor'] = []
    st.session_state['filtro_status'] = []
    st.rerun()

# Filtros Estratégicos (as caixas ficam vazias por padrão)
anos_selecionados = st.sidebar.multiselect("Ano:", options=anos_unicos, key='filtro_ano')
meses_selecionados = st.sidebar.multiselect("Mês:", options=meses_unicos, key='filtro_mes')
setores_selecionados = st.sidebar.multiselect("Setor:", options=setores_unicos, key='filtro_setor')
compradores_selecionados = st.sidebar.multiselect("Comprador:", options=compradores_unicos, key='filtro_comprador')
status_selecionados = st.sidebar.multiselect("Status do Prazo:", options=status_unicos, key='filtro_status')

# Nova Lógica de Filtragem: Se a caixa estiver vazia, não aplica o filtro
df_filtrado = df.copy()

if anos_selecionados:
    df_filtrado = df_filtrado[df_filtrado['ANO'].isin(anos_selecionados)]
if meses_selecionados:
    df_filtrado = df_filtrado[df_filtrado['MÊS REFERENTE'].isin(meses_selecionados)]
if compradores_selecionados:
    df_filtrado = df_filtrado[df_filtrado['COMPRADOR'].isin(compradores_selecionados)]
if setores_selecionados:
    df_filtrado = df_filtrado[df_filtrado['SETOR'].isin(setores_selecionados)]
if status_selecionados:
    df_filtrado = df_filtrado[df_filtrado['CATEGORIA_PRAZO'].isin(status_selecionados)]

# Botão de Exportação
st.sidebar.divider()
st.sidebar.title("Exportar Relatório")
@st.cache_data
def converter_df(df_export):
    return df_export.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')

csv_export = converter_df(df_filtrado)
st.sidebar.download_button(
    label="Baixar Dados Filtrados",
    data=csv_export,
    file_name='relatorio_compras_filtrado.csv',
    mime='text/csv'
)

# Créditos no Menu Lateral
st.sidebar.divider()
st.sidebar.markdown(
    """
    <div style="text-align: center; color: #888888; font-size: 13px; margin-top: 20px;">
        <p>Desenvolvido por <b>Waldir Neto</b></p>
        <p>Idealizado por <b>Weverton Andrade</b></p>
    </div>
    """, 
    unsafe_allow_html=True
)

# Cabeçalho do Dashboard
st.title("SUPPLY CHAIN ANALYTICS | Compras 360")
st.markdown("Portal de inteligência de compras e suprimentos.")

# Função auxiliar para formatar Reais
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# IA e Insights Automáticos
if not df_filtrado.empty:
    with st.expander("🤖 Robô de Insights Automáticos (Clique para abrir)", expanded=True):
        col_ia1, col_ia2 = st.columns(2)
        
        with col_ia1:
            top_comprador = df_filtrado.groupby('COMPRADOR')['SAVING COMPRADOR'].sum().idxmax()
            top_saving = df_filtrado.groupby('COMPRADOR')['SAVING COMPRADOR'].sum().max()
            st.success(f"💡 **Destaque de Economia:** O comprador(a) **{top_comprador}** gerou a maior economia desta seleção ({formatar_moeda(top_saving)}).")
            
        with col_ia2:
            if 'CATEGORIA_PRAZO' in df_filtrado.columns:
                df_atrasos_ia = df_filtrado[df_filtrado['CATEGORIA_PRAZO'] == 'Atrasado']
                if not df_atrasos_ia.empty:
                    pior_fornecedor = df_atrasos_ia['FORNECEDOR'].value_counts().idxmax()
                    qtd_atraso = df_atrasos_ia['FORNECEDOR'].value_counts().max()
                    st.error(f"⚠️ **Alerta de Risco:** O fornecedor **{pior_fornecedor}** é o mais crítico no momento, com {qtd_atraso} pedidos em atraso.")
                else:
                    st.info("✅ Excelente! Nenhum fornecedor em atraso nesta seleção.")

st.divider()

# KPIs
total_saving = df_filtrado['SAVING COMPRADOR'].sum()
total_pedidos = df_filtrado['Nº PEDIDO'].nunique()
total_fornecedores = df_filtrado['FORNECEDOR'].nunique()

taxa_sla = 0
if not df_filtrado.empty:
    df_sla_valido = df_filtrado[df_filtrado['CATEGORIA_PRAZO'] != 'Cancelado']
    if not df_sla_valido.empty:
        pedidos_no_prazo = len(df_sla_valido[df_sla_valido['CATEGORIA_PRAZO'].isin(['Finalizado', 'No Prazo'])])
        taxa_sla = (pedidos_no_prazo / len(df_sla_valido)) * 100

col1, col2, col3, col4, col5 = st.columns([1.8, 1.2, 1.1, 1.1, 1.1])
col1.metric("Economia Total (Saving)", formatar_moeda(total_saving))
col2.metric("🎯 Taxa de SLA (Sucesso)", f"{taxa_sla:.1f}%")
col3.metric("Total de Pedidos", total_pedidos)
col4.metric("Requisições", df_filtrado['Nº REQUISIÇÃO'].nunique())
col5.metric("Fornecedores Ativos", total_fornecedores)

st.divider()

# AS TRÊS ABAS DO SISTEMA
aba1, aba2, aba3 = st.tabs(["📊 Visão Geral", "⏱️ Análise de SLA e Prazos", "💰 Inteligência de Economia"])

with aba1:
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("Economia Gerada por Comprador")
        df_comprador = df_filtrado.groupby("COMPRADOR")['SAVING COMPRADOR'].sum().reset_index()
        df_comprador = df_comprador.sort_values(by="SAVING COMPRADOR", ascending=False)
        
        df_comprador['VALOR_FORMATADO'] = df_comprador['SAVING COMPRADOR'].apply(formatar_moeda)
        
        fig1 = px.bar(
            df_comprador, x="COMPRADOR", y="SAVING COMPRADOR", text="VALOR_FORMATADO",
            color_discrete_sequence=["#3B82F6"], labels={"SAVING COMPRADOR": "Economia (R$)", "COMPRADOR": "Comprador"}
        )
        fig1.update_traces(textposition='outside')
        fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        
        valor_maximo = df_comprador['SAVING COMPRADOR'].max()
        if pd.notna(valor_maximo) and valor_maximo > 0:
            fig1.update_yaxes(range=[0, valor_maximo * 1.2])
            
        st.plotly_chart(fig1, use_container_width=True)

    with col_graf2:
        st.subheader("Top Fornecedores (Por Volume de Pedidos)")
        df_fornecedor = df_filtrado['FORNECEDOR'].value_counts().reset_index().head(10)
        df_fornecedor.columns = ['FORNECEDOR', 'VOLUME']
        fig2 = px.pie(df_fornecedor, names='FORNECEDOR', values='VOLUME', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Tabela Operacional de Compras")
    colunas_exibicao = ['Nº PEDIDO', 'COMPRADOR', 'FORNECEDOR', 'SETOR', 'STATUS PRAZO', 'SAVING COMPRADOR']
    st.dataframe(df_filtrado[colunas_exibicao].head(100), use_container_width=True)

with aba2:
    st.subheader("Performance de Prazos (SLA)")
    col_sla1, col_sla2 = st.columns(2)
    
    with col_sla1:
        if 'CATEGORIA_PRAZO' in df_filtrado.columns:
            df_sla = df_filtrado['CATEGORIA_PRAZO'].value_counts().reset_index()
            df_sla.columns = ['STATUS', 'QUANTIDADE']
            mapa_cores = {"Finalizado": "#10B981", "No Prazo": "#3B82F6", "Atrasado": "#EF4444", "Cancelado": "#64748B", "Outros": "#F59E0B"}
            fig3 = px.bar(df_sla, x='STATUS', y='QUANTIDADE', color='STATUS', text_auto=True, color_discrete_map=mapa_cores)
            fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)
            
    with col_sla2:
        st.markdown("### 🔥 Top Fornecedores em Atraso")
        df_atrasados = df_filtrado[df_filtrado['CATEGORIA_PRAZO'] == 'Atrasado']
        if not df_atrasados.empty:
            fornecedores_atraso = df_atrasados['FORNECEDOR'].value_counts().reset_index()
            fornecedores_atraso.columns = ['Fornecedor', 'Quantidade de Atrasos']
            st.dataframe(fornecedores_atraso, use_container_width=True, hide_index=True)
        else:
            st.success("Excelente! Nenhum pedido em atraso encontrado.")

with aba3:
    st.subheader("Inteligência Financeira")
    col_sav1, col_sav2 = st.columns(2)
    
    with col_sav1:
        st.markdown("### Economia por Setor")
        if 'SETOR' in df_filtrado.columns:
            df_setor = df_filtrado.groupby('SETOR')['SAVING COMPRADOR'].sum().reset_index()
            df_setor = df_setor.sort_values(by='SAVING COMPRADOR', ascending=True).tail(10)
            
            df_setor['VALOR_FORMATADO'] = df_setor['SAVING COMPRADOR'].apply(formatar_moeda)
            
            fig4 = px.bar(
                df_setor, x='SAVING COMPRADOR', y='SETOR', orientation='h', 
                text='VALOR_FORMATADO', color_discrete_sequence=["#10B981"],
                labels={"SAVING COMPRADOR": "Economia (R$)", "SETOR": "Setor"}
            )
            fig4.update_traces(textposition='outside')
            fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            
            valor_max_setor = df_setor['SAVING COMPRADOR'].max()
            if pd.notna(valor_max_setor) and valor_max_setor > 0:
                fig4.update_xaxes(range=[0, valor_max_setor * 1.3])
                
            st.plotly_chart(fig4, use_container_width=True)
            
    with col_sav2:
        st.markdown("### Top Fornecedores por Economia Gerada")
        df_forn_sav = df_filtrado.groupby('FORNECEDOR')['SAVING COMPRADOR'].sum().reset_index()
        df_forn_sav = df_forn_sav.sort_values(by='SAVING COMPRADOR', ascending=False).head(10)
        
        df_forn_sav = df_forn_sav.rename(columns={'SAVING COMPRADOR': 'ECONOMIA GERADA'})
        st.dataframe(df_forn_sav.style.format({'ECONOMIA GERADA': 'R$ {:,.2f}'}), use_container_width=True, hide_index=True)
