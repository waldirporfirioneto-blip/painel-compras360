import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração da Página
st.set_page_config(page_title="Compras 360", layout="wide", page_icon="📊")

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

# Filtros Temporais
st.sidebar.divider()
st.sidebar.title("⚙️ Filtros da Operação")

anos_unicos = df['ANO'].dropna().unique().tolist()
anos_unicos = sorted(anos_unicos, reverse=True)
anos_selecionados = st.sidebar.multiselect("📅 Selecione o Ano:", options=anos_unicos, default=anos_unicos)

meses_unicos = df['MÊS REFERENTE'].dropna().unique().tolist()
meses_selecionados = st.sidebar.multiselect("📆 Selecione o Mês:", options=meses_unicos, default=meses_unicos)

compradores_unicos = df['COMPRADOR'].dropna().unique().tolist()
compradores_selecionados = st.sidebar.multiselect("👤 Selecione o Comprador:", options=compradores_unicos, default=compradores_unicos)

df_filtrado = df[
    (df['ANO'].isin(anos_selecionados)) &
    (df['MÊS REFERENTE'].isin(meses_selecionados)) &
    (df['COMPRADOR'].isin(compradores_selecionados))
]

# Botão de Exportação
st.sidebar.divider()
st.sidebar.title("📥 Exportar Relatório")
@st.cache_data
def converter_df(df):
    return df.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')

csv_export = converter_df(df_filtrado)
st.sidebar.download_button(
    label="Baixar Dados Filtrados (Excel/CSV)",
    data=csv_export,
    file_name='relatorio_compras_filtrado.csv',
    mime='text/csv'
)

# NOVO: Créditos no Menu Lateral
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

# IA e Insights Automáticos
if not df_filtrado.empty:
    with st.expander("🤖 Robô de Insights Automáticos (Clique para abrir)", expanded=True):
        col_ia1, col_ia2 = st.columns(2)
        
        with col_ia1:
            top_comprador = df_filtrado.groupby('COMPRADOR')['SAVING COMPRADOR'].sum().idxmax()
            top_saving = df_filtrado.groupby('COMPRADOR')['SAVING COMPRADOR'].sum().max()
            st.success(f"💡 **Destaque de Economia:** O comprador(a) **{top_comprador}** gerou o maior saving desta seleção (R$ {top_saving:,.2f}).")
            
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

# Cálculo de KPIs
total_saving = df_filtrado['SAVING COMPRADOR'].sum()
total_pedidos = df_filtrado['Nº PEDIDO'].nunique()
total_requisicoes = df_filtrado['Nº REQUISIÇÃO'].nunique()
total_fornecedores = df_filtrado['FORNECEDOR'].nunique()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Saving Total", f"R$ {total_saving:,.2f}")
col2.metric("Total de Pedidos", total_pedidos)
col3.metric("Requisições", total_requisicoes)
col4.metric("Fornecedores Ativos", total_fornecedores)

st.divider()

# AS TRÊS ABAS DO SISTEMA
aba1, aba2, aba3 = st.tabs(["📊 Visão Geral", "⏱️ Análise de SLA e Prazos", "💰 Saving Intelligence"])

with aba1:
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("Saving por Comprador")
        df_comprador = df_filtrado.groupby("COMPRADOR")['SAVING COMPRADOR'].sum().reset_index()
        df_comprador = df_comprador.sort_values(by="SAVING COMPRADOR", ascending=False)
        fig1 = px.bar(df_comprador, x="COMPRADOR", y="SAVING COMPRADOR", color_discrete_sequence=["#3B82F6"], text_auto=".2s")
        fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
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
    st.subheader("Inteligência Financeira (Saving)")
    col_sav1, col_sav2 = st.columns(2)
    
    with col_sav1:
        st.markdown("### Saving por Setor")
        if 'SETOR' in df_filtrado.columns:
            df_setor = df_filtrado.groupby('SETOR')['SAVING COMPRADOR'].sum().reset_index()
            df_setor = df_setor.sort_values(by='SAVING COMPRADOR', ascending=True).tail(10)
            fig4 = px.bar(df_setor, x='SAVING COMPRADOR', y='SETOR', orientation='h', color_discrete_sequence=["#10B981"], text_auto=".2s")
            fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig4, use_container_width=True)
            
    with col_sav2:
        st.markdown("### Top Fornecedores por Saving")
        df_forn_sav = df_filtrado.groupby('FORNECEDOR')['SAVING COMPRADOR'].sum().reset_index()
        df_forn_sav = df_forn_sav.sort_values(by='SAVING COMPRADOR', ascending=False).head(10)
        st.dataframe(df_forn_sav.style.format({'SAVING COMPRADOR': 'R$ {:,.2f}'}), use_container_width=True, hide_index=True)
