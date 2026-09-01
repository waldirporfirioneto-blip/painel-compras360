import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# 1. Configuração da Página
st.set_page_config(page_title="Compras 360", layout="wide", page_icon="📊")

# Esconder o ícone de olho do navegador
st.markdown(
    """
    <style>
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

# Atualização de Dados
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
        df['ANO'] = df['ANO'].fillna(0).astype(int).astype(str).replace('0', 'Não Informado')
        
    # --- NOVO: Lógica de Vencimento em Tempo Real ---
    if 'PRAZO RC' in df.columns and 'STATUS PRAZO' in df.columns:
        df['PRAZO RC'] = pd.to_datetime(df['PRAZO RC'], errors='coerce')
        hoje = pd.to_datetime(datetime.now().date())
        
        def analisar_prazo_real(row):
            status = str(row['STATUS PRAZO']).strip().upper()
            data_prazo = row['PRAZO RC']
            
            if "FINALIZADO" in status:
                return "Finalizado", "Entregue"
            elif "CANCELADO" in status:
                return "Cancelado", "Cancelado"
            elif pd.isna(data_prazo):
                return "Outros", "Sem Data"
            else:
                diferenca_dias = (data_prazo - hoje).days
                if diferenca_dias < 0:
                    return "Atrasado", f"Vencido há {abs(diferenca_dias)} dias"
                elif diferenca_dias == 0:
                    return "No Prazo", "Vence Hoje!"
                else:
                    return "No Prazo", f"Faltam {diferenca_dias} dias"
                    
        resultado = df.apply(analisar_prazo_real, axis=1)
        df['CATEGORIA_PRAZO'] = [res[0] for res in resultado]
        df['DESCRICAO_VENCIMENTO'] = [res[1] for res in resultado]
    else:
        # Fallback caso não tenha as colunas de data
        df['CATEGORIA_PRAZO'] = "Outros"
        df['DESCRICAO_VENCIMENTO'] = "Sem Dados de Data"
        
    return df

df = carregar_dados(arquivo_upload)

# Configurando Filtros
anos_unicos = sorted(df['ANO'].dropna().unique().tolist(), reverse=True)
meses_unicos = df['MÊS REFERENTE'].dropna().unique().tolist()
compradores_unicos = df['COMPRADOR'].dropna().unique().tolist()
setores_unicos = df['SETOR'].dropna().unique().tolist() if 'SETOR' in df.columns else []
status_unicos = df['CATEGORIA_PRAZO'].dropna().unique().tolist() if 'CATEGORIA_PRAZO' in df.columns else []

if 'filtro_ano' not in st.session_state: st.session_state['filtro_ano'] = []
if 'filtro_mes' not in st.session_state: st.session_state['filtro_mes'] = []
if 'filtro_comprador' not in st.session_state: st.session_state['filtro_comprador'] = []
if 'filtro_setor' not in st.session_state: st.session_state['filtro_setor'] = []
if 'filtro_status' not in st.session_state: st.session_state['filtro_status'] = []

st.sidebar.divider()
st.sidebar.title("⚙️ Filtros da Operação")

if st.sidebar.button("🧹 Limpar Todos os Filtros"):
    st.session_state['filtro_ano'] = []
    st.session_state['filtro_mes'] = []
    st.session_state['filtro_comprador'] = []
    st.session_state['filtro_setor'] = []
    st.session_state['filtro_status'] = []
    st.rerun()

anos_selecionados = st.sidebar.multiselect("📅 Ano:", options=anos_unicos, key='filtro_ano')
meses_selecionados = st.sidebar.multiselect("📆 Mês:", options=meses_unicos, key='filtro_mes')
setores_selecionados = st.sidebar.multiselect("🏭 Setor:", options=setores_unicos, key='filtro_setor')
compradores_selecionados = st.sidebar.multiselect("👤 Comprador:", options=compradores_unicos, key='filtro_comprador')
status_selecionados = st.sidebar.multiselect("⏱️ Status do Prazo:", options=status_unicos, key='filtro_status')

df_filtrado = df.copy()

if anos_selecionados: df_filtrado = df_filtrado[df_filtrado['ANO'].isin(anos_selecionados)]
if meses_selecionados: df_filtrado = df_filtrado[df_filtrado['MÊS REFERENTE'].isin(meses_selecionados)]
if compradores_selecionados: df_filtrado = df_filtrado[df_filtrado['COMPRADOR'].isin(compradores_selecionados)]
if setores_selecionados: df_filtrado = df_filtrado[df_filtrado['SETOR'].isin(setores_selecionados)]
if status_selecionados: df_filtrado = df_filtrado[df_filtrado['CATEGORIA_PRAZO'].isin(status_selecionados)]

# --- NOVO: Exportação Formatada e Limpa ---
st.sidebar.divider()
st.sidebar.title("📥 Exportar Relatório")

@st.cache_data
def preparar_exportacao(df_exp):
    df_clean = df_exp.copy()
    if 'PRAZO RC' in df_clean.columns:
        df_clean['PRAZO RC'] = df_clean['PRAZO RC'].dt.strftime('%d/%m/%Y')
    return df_clean.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')

csv_export = preparar_exportacao(df_filtrado)
st.sidebar.download_button(
    label="Baixar Dados Formatados (Excel/CSV)",
    data=csv_export,
    file_name=f'relatorio_compras_{datetime.now().strftime("%Y%m%d")}.csv',
    mime='text/csv'
)

# Créditos
st.sidebar.divider()
st.sidebar.markdown(
    """
    <div style="text-align: center; color: #888888; font-size: 13px; margin-top: 20px;">
        <p>Desenvolvido por <b>Waldir Neto</b></p>
        <p>Idealizado por <b>Weverton Andrade</b></p>
    </div>
    """, unsafe_allow_html=True
)

# Cabeçalho Principal
st.title("SUPPLY CHAIN ANALYTICS | Compras 360")
st.markdown("Portal de inteligência de compras e acompanhamento de SLA.")

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# --- NOVO: Robô de Insights Turbinado com Metas Batidas ---
if not df_filtrado.empty:
    with st.expander("🤖 Robô de Insights Automáticos", expanded=True):
        col_ia1, col_ia2, col_ia3 = st.columns(3)
        
        with col_ia1:
            top_comprador = df_filtrado.groupby('COMPRADOR')['SAVING COMPRADOR'].sum().idxmax()
            top_saving = df_filtrado.groupby('COMPRADOR')['SAVING COMPRADOR'].sum().max()
            st.success(f"🏆 **Líder de Economia:** {top_comprador} gerou a maior economia total ({formatar_moeda(top_saving)}).")
            
        with col_ia2:
            # Conta compras únicas com saving > 5000
            df_metas = df_filtrado[df_filtrado['SAVING COMPRADOR'] > 5000]
            if not df_metas.empty:
                campeao_metas = df_metas['COMPRADOR'].value_counts().idxmax()
                qtd_metas = df_metas['COMPRADOR'].value_counts().max()
                st.info(f"🎯 **Bateu a Meta (>R$ 5K):** {campeao_metas} conseguiu {qtd_metas} grandes negociações.")
            else:
                st.info("🎯 Nenhuma compra acima da meta de R$ 5.000 nesta seleção.")
                
        with col_ia3:
            df_atrasos_ia = df_filtrado[df_filtrado['CATEGORIA_PRAZO'] == 'Atrasado']
            if not df_atrasos_ia.empty:
                pior_fornecedor = df_atrasos_ia['FORNECEDOR'].value_counts().idxmax()
                qtd_atraso = df_atrasos_ia['FORNECEDOR'].value_counts().max()
                st.error(f"⚠️ **Risco Iminente:** Fornecedor {pior_fornecedor} possui {qtd_atraso} pedidos atrasados.")
            else:
                st.success("✅ Nenhum fornecedor em atraso nesta seleção.")

st.divider()

# KPIs Superiores
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
aba1, aba2, aba3 = st.tabs(["💰 Economia & Metas", "⏱️ Painel de Vencimentos (Tempo Real)", "📊 Visão Geral Operacional"])

with aba1:
    st.subheader("Performance Financeira da Equipe")
    col_eco1, col_eco2 = st.columns(2)
    
    with col_eco1:
        st.markdown("### Economia Total por Comprador")
        df_comprador = df_filtrado.groupby("COMPRADOR")['SAVING COMPRADOR'].sum().reset_index()
        df_comprador = df_comprador.sort_values(by="SAVING COMPRADOR", ascending=False)
        df_comprador['VALOR_FORMATADO'] = df_comprador['SAVING COMPRADOR'].apply(formatar_moeda)
        
        fig1 = px.bar(
            df_comprador, x="COMPRADOR", y="SAVING COMPRADOR", text="VALOR_FORMATADO",
            color_discrete_sequence=["#10B981"], labels={"SAVING COMPRADOR": "Economia (R$)", "COMPRADOR": "Comprador"}
        )
        fig1.update_traces(textposition='outside')
        fig1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        if df_comprador['SAVING COMPRADOR'].max() > 0:
            fig1.update_yaxes(range=[0, df_comprador['SAVING COMPRADOR'].max() * 1.2])
        st.plotly_chart(fig1, use_container_width=True)
        
    with col_eco2:
        st.markdown("### 🏆 Ranking: Metas Batidas (> R$ 5.000)")
        df_metas_rank = df_filtrado[df_filtrado['SAVING COMPRADOR'] > 5000]
        if not df_metas_rank.empty:
            rank_compradores = df_metas_rank['COMPRADOR'].value_counts().reset_index()
            rank_compradores.columns = ['Comprador', 'Qtd Negociações Extras']
            st.dataframe(rank_compradores, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma negociação acima de R$ 5.000 na visão atual.")
            
    st.markdown("### Top Fornecedores que mais geram economia")
    df_forn_sav = df_filtrado.groupby('FORNECEDOR')['SAVING COMPRADOR'].sum().reset_index()
    df_forn_sav = df_forn_sav.sort_values(by='SAVING COMPRADOR', ascending=False).head(5)
    st.dataframe(df_forn_sav.rename(columns={'SAVING COMPRADOR': 'ECONOMIA GERADA'}).style.format({'ECONOMIA GERADA': 'R$ {:,.2f}'}), use_container_width=True, hide_index=True)

# --- NOVO: Aba Dedicada de Vencimentos em Tempo Real ---
with aba2:
    st.subheader("Controle Dinâmico de Entregas")
    
    col_ven1, col_ven2 = st.columns(2)
    with col_ven1:
        st.markdown("### Distribuição de Status")
        if 'CATEGORIA_PRAZO' in df_filtrado.columns:
            df_sla = df_filtrado['CATEGORIA_PRAZO'].value_counts().reset_index()
            df_sla.columns = ['STATUS', 'QUANTIDADE']
            mapa_cores = {"Finalizado": "#10B981", "No Prazo": "#3B82F6", "Atrasado": "#EF4444", "Cancelado": "#64748B", "Outros": "#F59E0B"}
            fig3 = px.pie(df_sla, names='STATUS', values='QUANTIDADE', color='STATUS', hole=0.4, color_discrete_map=mapa_cores)
            fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig3, use_container_width=True)
            
    with col_ven2:
        st.markdown("### 🔴 Painel Crítico: Pedidos em Atraso")
        df_pendentes = df_filtrado[df_filtrado['CATEGORIA_PRAZO'] == 'Atrasado'][['Nº PEDIDO', 'FORNECEDOR', 'COMPRADOR', 'DESCRICAO_VENCIMENTO']]
        if not df_pendentes.empty:
            st.dataframe(df_pendentes, use_container_width=True, hide_index=True)
        else:
            st.success("Sem atrasos no momento!")
            
    st.markdown("### 🟡 Radar: Vencendo nos próximos 15 dias")
    if 'CATEGORIA_PRAZO' in df_filtrado.columns:
        df_radar = df_filtrado[df_filtrado['CATEGORIA_PRAZO'] == 'No Prazo'][['Nº PEDIDO', 'FORNECEDOR', 'COMPRADOR', 'DESCRICAO_VENCIMENTO']]
        # Filtra textualmente os que têm "Faltam" e estão perto
        df_radar = df_radar[df_radar['DESCRICAO_VENCIMENTO'].str.contains("Vence|Faltam", na=False)]
        st.dataframe(df_radar, use_container_width=True, hide_index=True)

with aba3:
    st.subheader("Mapeamento da Operação")
    col_op1, col_op2 = st.columns(2)
    
    with col_op1:
        st.markdown("### Volume por Setor Solicitante")
        if 'SETOR' in df_filtrado.columns:
            df_setor_vol = df_filtrado['SETOR'].value_counts().reset_index().head(10)
            df_setor_vol.columns = ['SETOR', 'REQUISIÇÕES']
            fig_setor = px.bar(df_setor_vol, x='SETOR', y='REQUISIÇÕES', color_discrete_sequence=["#8B5CF6"])
            fig_setor.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_setor, use_container_width=True)
            
    with col_op2:
        st.markdown("### Concentração de Pedidos por Fornecedor")
        df_fornecedor = df_filtrado['FORNECEDOR'].value_counts().reset_index().head(10)
        df_fornecedor.columns = ['FORNECEDOR', 'VOLUME']
        fig2 = px.bar(df_fornecedor, y='FORNECEDOR', x='VOLUME', orientation='h', color_discrete_sequence=["#F59E0B"])
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### Visão Detalhada")
    colunas_exibicao = ['Nº PEDIDO', 'COMPRADOR', 'FORNECEDOR', 'SETOR', 'STATUS PRAZO', 'DESCRICAO_VENCIMENTO']
    st.dataframe(df_filtrado[colunas_exibicao].head(100), use_container_width=True)
