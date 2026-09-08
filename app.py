import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# 1. Configuração da Página
st.set_page_config(page_title="Compras 360", layout="wide", page_icon="📊")

# Esconder o ícone de olho do navegador para não duplicar na senha
st.markdown(
    """
    <style>
    input[type="password"]::-ms-reveal,
    input[type="password"]::-ms-clear {
        display: none;
    }
    .stDataFrame { padding-top: 10px; }
    </style>
    """,
    unsafe_allow_html=True
)

# Identidade Visual
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
else:
    st.sidebar.markdown("<h2 style='text-align: center; color: #10B981;'>🏢 GREE ELECTRIC</h2>", unsafe_allow_html=True)

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
        
    if 'PRAZO RC' in df.columns and 'STATUS PRAZO' in df.columns:
        df['PRAZO RC'] = pd.to_datetime(df['PRAZO RC'], errors='coerce')
        hoje = pd.to_datetime(datetime.now().date())
        
        def analisar_prazo_real(row):
            status = str(row['STATUS PRAZO']).strip().upper()
            data_prazo = row['PRAZO RC']
            
            if "FINALIZADO" in status: return "Finalizado", "Entregue"
            elif "CANCELADO" in status: return "Cancelado", "Cancelado"
            elif pd.isna(data_prazo): return "Outros", "Sem Data"
            else:
                diferenca_dias = (data_prazo - hoje).days
                if diferenca_dias < 0: return "Atrasado", f"Vencido há {abs(diferenca_dias)} dias"
                elif diferenca_dias == 0: return "No Prazo", "Vence Hoje!"
                else: return "No Prazo", f"Faltam {diferenca_dias} dias"
                    
        resultado = df.apply(analisar_prazo_real, axis=1)
        df['CATEGORIA_PRAZO'] = [res[0] for res in resultado]
        df['DESCRICAO_VENCIMENTO'] = [res[1] for res in resultado]
    else:
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
    for key in ['filtro_ano', 'filtro_mes', 'filtro_comprador', 'filtro_setor', 'filtro_status']:
        st.session_state[key] = []
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

# Exportação Formatada
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
    label="Baixar Dados Formatados",
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

# Função para resumir valores no gráfico (ex: R$ 260K)
def formatar_k(valor):
    if valor >= 1000:
        return f"R$ {valor/1000:.1f}K".replace(".", ",")
    return f"R$ {valor:,.0f}".replace(",", ".")

# IA e Insights Automáticos
if not df_filtrado.empty:
    with st.expander("🤖 Robô de Insights Automáticos", expanded=True):
        col_ia1, col_ia2, col_ia3 = st.columns(3)
        with col_ia1:
            top_comprador = df_filtrado.groupby('COMPRADOR')['SAVING COMPRADOR'].sum().idxmax()
            top_saving = df_filtrado.groupby('COMPRADOR')['SAVING COMPRADOR'].sum().max()
            st.success(f"🏆 **Líder de Economia:** {top_comprador} ({formatar_moeda(top_saving)}).")
        with col_ia2:
            df_metas = df_filtrado[df_filtrado['SAVING COMPRADOR'] >= 5000]
            if not df_metas.empty:
                campeao_metas = df_metas['COMPRADOR'].value_counts().idxmax()
                qtd_metas = df_metas['COMPRADOR'].value_counts().max()
                st.info(f"🎯 **Metas Batidas (>R$ 5K):** {campeao_metas} lidera com {qtd_metas} hits.")
            else:
                st.info("🎯 Nenhuma compra acima da meta nesta seleção.")
        with col_ia3:
            df_atrasos_ia = df_filtrado[df_filtrado['CATEGORIA_PRAZO'] == 'Atrasado']
            if not df_atrasos_ia.empty:
                pior_fornecedor = df_atrasos_ia['FORNECEDOR'].value_counts().idxmax()
                qtd_atraso = df_atrasos_ia['FORNECEDOR'].value_counts().max()
                st.error(f"⚠️ **Risco:** Fornecedor '{pior_fornecedor}' possui {qtd_atraso} pedidos atrasados.")
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

# ABAS DO SISTEMA
aba1, aba2, aba3 = st.tabs(["💰 Economia & Metas", "⏱️ Vencimentos & Cobrança", "⭐ Avaliação de Fornecedores"])

# --- ABA 1: NOVO LAYOUT VERTICAL E EM CASCATA ---
with aba1:
    st.subheader("Economia Total por Comprador")
    
    # 1. Gráfico no topo, ocupando toda a largura
    df_comprador = df_filtrado.groupby("COMPRADOR")['SAVING COMPRADOR'].sum().reset_index()
    df_comprador = df_comprador.sort_values(by="SAVING COMPRADOR", ascending=False)
    
    # Aplica a formatação limpa "K" para o gráfico
    df_comprador['TEXTO_GRAFICO'] = df_comprador['SAVING COMPRADOR'].apply(formatar_k)
    
    fig1 = px.bar(
        df_comprador, x="COMPRADOR", y="SAVING COMPRADOR", text="TEXTO_GRAFICO",
        color_discrete_sequence=["#10B981"], height=350
    )
    fig1.update_traces(textposition='outside', textfont_size=12)
    fig1.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(showgrid=False, showticklabels=False, title=""), # Limpa o eixo Y
        xaxis=dict(title="", tickfont_size=14, tickangle=0), # Texto na horizontal se couber
        margin=dict(l=0, r=0, t=20, b=0)
    )
    if df_comprador['SAVING COMPRADOR'].max() > 0:
        fig1.update_yaxes(range=[0, df_comprador['SAVING COMPRADOR'].max() * 1.2])
    
    st.plotly_chart(fig1, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True) # Espaço
    
    # 2. Tabelas lado a lado na parte de baixo
    col_rank1, col_rank2 = st.columns(2)
    
    with col_rank1:
        st.markdown("### 🏆 Ranking: Metas Batidas (> R$ 5.000)")
        df_metas_rank = df_filtrado[df_filtrado['SAVING COMPRADOR'] >= 5000]
        if not df_metas_rank.empty:
            rank_compradores = df_metas_rank['COMPRADOR'].value_counts().reset_index()
            rank_compradores.columns = ['Comprador', 'Qtd Negociações']
            st.dataframe(rank_compradores, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma negociação acima da meta.")
            
    with col_rank2:
        st.markdown("### 🔝 Top Fornecedores (Economia Gerada)")
        df_forn_sav = df_filtrado.groupby('FORNECEDOR')['SAVING COMPRADOR'].sum().reset_index()
        df_forn_sav = df_forn_sav.sort_values(by='SAVING COMPRADOR', ascending=False).head(5)
        st.dataframe(df_forn_sav.rename(columns={'SAVING COMPRADOR': 'Economia'}).style.format({'Economia': 'R$ {:,.2f}'}), use_container_width=True, hide_index=True)

# --- ABA 2: VENCIMENTOS (Mantida e Melhorada) ---
with aba2:
    st.subheader("Controle Dinâmico de Entregas e Ferramentas")
    
    with st.container():
        st.markdown("### 💬 Assistente de Cobrança (WhatsApp)")
        df_atrasados_lista = df_filtrado[df_filtrado['CATEGORIA_PRAZO'] == 'Atrasado']
        
        if not df_atrasados_lista.empty:
            col_msg1, col_msg2 = st.columns([1, 2])
            with col_msg1:
                pedido_sel = st.selectbox("Selecione o Pedido em atraso:", df_atrasados_lista['Nº PEDIDO'].unique())
            
            with col_msg2:
                dados_pedido = df_atrasados_lista[df_atrasados_lista['Nº PEDIDO'] == pedido_sel].iloc[0]
                desc_item = dados_pedido.get('DESCRIÇÃO DO ITEM ', 'Material solicitado')
                
                mensagem = f"Olá, equipe da *{dados_pedido['FORNECEDOR']}*.\n\nConsta em nosso sistema de suprimentos que o Pedido *{pedido_sel}* ({desc_item}) encontra-se *{dados_pedido['DESCRICAO_VENCIMENTO']}*.\n\nGostaríamos de um posicionamento urgente sobre a previsão de entrega.\n\n*Suprimentos - Gree Electric*"
                st.code(mensagem, language="text")
        else:
            st.success("Não há pedidos atrasados para cobrar no momento. Ótimo trabalho!")
            
    st.divider()

    col_ven1, col_ven2 = st.columns([1.5, 2])
    with col_ven1:
        st.markdown("### Distribuição de Status")
        if 'CATEGORIA_PRAZO' in df_filtrado.columns:
            df_sla = df_filtrado['CATEGORIA_PRAZO'].value_counts().reset_index()
            df_sla.columns = ['STATUS', 'QUANTIDADE']
            mapa_cores = {"Finalizado": "#10B981", "No Prazo": "#3B82F6", "Atrasado": "#EF4444", "Cancelado": "#64748B", "Outros": "#F59E0B"}
            fig3 = px.pie(df_sla, names='STATUS', values='QUANTIDADE', color='STATUS', hole=0.5, color_discrete_map=mapa_cores)
            fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig3, use_container_width=True)
            
    with col_ven2:
        st.markdown("### 🔴 Painel Crítico: Atrasados")
        if not df_atrasados_lista.empty:
            st.dataframe(df_atrasados_lista[['Nº PEDIDO', 'FORNECEDOR', 'COMPRADOR', 'DESCRICAO_VENCIMENTO']], use_container_width=True, hide_index=True, height=200)
        else:
            st.info("Sem atrasos no momento.")
            
        st.markdown("### 🟡 Radar: Vencendo nos próximos 15 dias")
        if 'CATEGORIA_PRAZO' in df_filtrado.columns:
            df_radar = df_filtrado[df_filtrado['CATEGORIA_PRAZO'] == 'No Prazo'][['Nº PEDIDO', 'FORNECEDOR', 'COMPRADOR', 'DESCRICAO_VENCIMENTO']]
            df_radar = df_radar[df_radar['DESCRICAO_VENCIMENTO'].str.contains("Vence|Faltam", na=False)]
            st.dataframe(df_radar, use_container_width=True, hide_index=True, height=200)

# --- ABA 3: AVALIAÇÃO DE FORNECEDORES ---
with aba3:
    st.subheader("Avaliação de Fornecedores e Demanda")
    
    col_op1, col_op2 = st.columns([1.2, 1.8])
    with col_op1:
        st.markdown("### 🏭 Demanda por Setor")
        if 'SETOR' in df_filtrado.columns:
            df_setor_vol = df_filtrado['SETOR'].value_counts().reset_index().head(10)
            df_setor_vol.columns = ['SETOR', 'REQUISIÇÕES']
            # Gráfico de barras horizontal mais limpo
            fig_setor = px.bar(df_setor_vol, x='REQUISIÇÕES', y='SETOR', orientation='h', color_discrete_sequence=["#8B5CF6"])
            fig_setor.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", 
                yaxis=dict(autorange="reversed", title=""),
                xaxis=dict(title="", showgrid=False)
            )
            st.plotly_chart(fig_setor, use_container_width=True)
            
    with col_op2:
        st.markdown("### ⭐ Score de Risco de Fornecedores")
        st.markdown("Cruza volume total de pedidos com falhas de entrega.")
        if not df_filtrado.empty:
            df_forn_total = df_filtrado.groupby('FORNECEDOR').size().reset_index(name='Total Pedidos')
            df_forn_atrasos = df_filtrado[df_filtrado['CATEGORIA_PRAZO'] == 'Atrasado'].groupby('FORNECEDOR').size().reset_index(name='Qtd Atrasos')
            
            df_score = pd.merge(df_forn_total, df_forn_atrasos, on='FORNECEDOR', how='left').fillna(0)
            df_score['Taxa Falha'] = df_score['Qtd Atrasos'] / df_score['Total Pedidos']
            
            def gerar_nota(linha):
                if linha['Taxa Falha'] == 0: return "A ⭐⭐⭐"
                elif linha['Taxa Falha'] <= 0.2: return "B ⭐⭐"
                elif linha['Taxa Falha'] <= 0.5: return "C ⭐"
                else: return "D ⚠️"
                
            df_score['Classificação'] = df_score.apply(gerar_nota, axis=1)
            df_score = df_score.sort_values(by=['Total Pedidos', 'Taxa Falha'], ascending=[False, True]).head(15)
            
            st.dataframe(
                df_score[['FORNECEDOR', 'Classificação', 'Total Pedidos', 'Qtd Atrasos']], 
                use_container_width=True, 
                hide_index=True,
                height=350
            )
