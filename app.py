import streamlit as st
import pandas as pd
import plotly.express as px
import time
import xlsxwriter

# Configuração inicial do app deve ser o PRIMEIRO comando após os imports
st.set_page_config(page_title="Gerenciador Financeiro", layout="wide")

# Inicializando listas para receitas e despesas
if "receitas" not in st.session_state:
    st.session_state.receitas = []
if "despesas" not in st.session_state:
    st.session_state.despesas = []

# Função para calcular totais
def calcular_totais():
    total_receitas = sum([item['valor'] for item in st.session_state.receitas])
    total_despesas = sum([item['valor'] for item in st.session_state.despesas])
    saldo = total_receitas - total_despesas
    return total_receitas, total_despesas, saldo

# Função para exibir gráficos no Resumo
def exibir_graficos_resumo():
    total_receitas, total_despesas, saldo = calcular_totais()

    # Gráfico de barras para despesas
    if st.session_state.despesas:
        df_despesas = pd.DataFrame(st.session_state.despesas)
        categorias = df_despesas.groupby("categoria")["valor"].sum().reset_index()
        fig_bar = px.bar(
            categorias, 
            x="categoria", 
            y="valor", 
            title="Despesas por Categoria", 
            color="categoria",
            template="plotly_white", 
            text="valor"
        )
        fig_bar.update_traces(texttemplate='R$ %{text:.2f}', textposition='outside')
        st.plotly_chart(fig_bar)

        # Gráfico Treemap
        categorias_treemap = categorias.copy()
        categorias_treemap["Tipo"] = "Despesas"
        receitas_df = pd.DataFrame([{"categoria": "Receitas Totais", "valor": total_receitas, "Tipo": "Receitas"}])
        consolidado = pd.concat([categorias_treemap, receitas_df])
        consolidado["label"] = consolidado["categoria"] + "<br>R$ " + consolidado["valor"].astype(str)
        fig_treemap = px.treemap(
            consolidado,
            path=["Tipo", "label"],
            values="valor",
            title="Treemap - Receitas e Despesas",
            color="Tipo",
            color_discrete_map={"Receitas": "#4CAF50", "Despesas": "#FF5722"}
        )
        st.plotly_chart(fig_treemap)

# Função para exportar relatório detalhado para Excel
def exportar_excel_detalhado():
    df_receitas = pd.DataFrame(st.session_state.receitas)
    df_despesas = pd.DataFrame(st.session_state.despesas)
    total_receitas, total_despesas, saldo = calcular_totais()

    with pd.ExcelWriter("relatorio_financeiro_detalhado.xlsx", engine="xlsxwriter") as writer:
        # Aba de Resumo
        resumo = pd.DataFrame({
            "Descrição": ["Total de Receitas", "Total de Despesas", "Saldo Final"],
            "Valor (R$)": [total_receitas, total_despesas, saldo]
        })
        resumo.to_excel(writer, sheet_name="Resumo", index=False)

        # Formatação e gráficos no Excel
        workbook = writer.book
        worksheet_resumo = writer.sheets["Resumo"]
        currency_format = workbook.add_format({"num_format": "R$ #,##0.00", "bold": True, "align": "center"})
        header_format = workbook.add_format({"bold": True, "align": "center", "bg_color": "#6C63FF", "color": "white"})
        worksheet_resumo.set_column("A:A", 30, None)
        worksheet_resumo.set_column("B:B", 20, currency_format)
        worksheet_resumo.write_row("A1", resumo.columns, header_format)

        chart = workbook.add_chart({"type": "column"})
        chart.add_series({
            "categories": ["Resumo", 1, 0, 3, 0],
            "values": ["Resumo", 1, 1, 3, 1],
            "name": "Resumo Financeiro"
        })
        chart.set_title({"name": "Resumo Financeiro"})
        worksheet_resumo.insert_chart("D2", chart)

        # Receitas e Despesas
        if not df_receitas.empty:
            df_receitas.to_excel(writer, sheet_name="Receitas", index=False)
            worksheet_receitas = writer.sheets["Receitas"]
            worksheet_receitas.set_column("A:A", 40)
            worksheet_receitas.set_column("B:B", 20, currency_format)
            worksheet_receitas.write_row("A1", df_receitas.columns, header_format)

        if not df_despesas.empty:
            df_despesas.to_excel(writer, sheet_name="Despesas", index=False)
            worksheet_despesas = writer.sheets["Despesas"]
            worksheet_despesas.set_column("A:A", 40)
            worksheet_despesas.set_column("B:B", 20, currency_format)
            worksheet_despesas.set_column("C:C", 20)
            worksheet_despesas.write_row("A1", df_despesas.columns, header_format)

    with open("relatorio_financeiro_detalhado.xlsx", "rb") as file:
        st.download_button(
            label="📥 Baixar Relatório Detalhado",
            data=file,
            file_name="relatorio_financeiro_detalhado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Menu lateral
menu = ["🏠 Início", "➕ Adicionar Receita", "➖ Adicionar Despesa", "📊 Resumo", "📁 Exportar Relatório"]
escolha = st.sidebar.radio("Menu", menu)

# Menu de navegação
if escolha == "🏠 Início":
    st.markdown('<h1 class="big-font centered"> Gerenciador Financeiro Empresarial </h1>', unsafe_allow_html=True)
    st.write(
        """
        Este aplicativo foi projetado para simplificar o gerenciamento financeiro e fornecer insights claros sobre suas finanças. 
        - **Receitas**: Adicione fontes de receita.
        - **Despesas**: Registre e categorize suas despesas.
        - **Resumo Financeiro**: Obtenha uma visão clara com gráficos interativos.
        - **Relatórios Exportáveis**: Baixe os dados em Excel.
        """
    )

elif escolha == "➕ Adicionar Receita":
    st.subheader("Adicionar Receita")
    descricao = st.text_input("Descrição da Receita")
    valor = st.number_input("Valor", min_value=0.0, step=0.01)
    if st.button("💾 Adicionar Receita"):
        if descricao and valor > 0:
            st.session_state.receitas.append({"descricao": descricao, "valor": valor})
            st.success("Receita adicionada com sucesso!")
        else:
            st.error("Por favor, preencha todos os campos corretamente.")

elif escolha == "➖ Adicionar Despesa":
    st.subheader("Adicionar Despesa")
    descricao = st.text_input("Descrição da Despesa")
    valor = st.number_input("Valor", min_value=0.0, step=0.01)
    categoria = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Outros"])
    if st.button("💾 Adicionar Despesa"):
        if descricao and valor > 0:
            st.session_state.despesas.append({"descricao": descricao, "valor": valor, "categoria": categoria})
            st.success("Despesa adicionada com sucesso!")
        else:
            st.error("Por favor, preencha todos os campos corretamente.")

elif escolha == "📊 Resumo":
    st.subheader("Resumo Financeiro")
    total_receitas, total_despesas, saldo = calcular_totais()
    col1, col2, col3 = st.columns(3)
    col1.metric("Receitas", f"R${total_receitas:.2f}")
    col2.metric("Despesas", f"R${total_despesas:.2f}")
    col3.metric("Saldo", f"R${saldo:.2f}")
    exibir_graficos_resumo()

elif escolha == "📁 Exportar Relatório":
    st.subheader("Exportar Relatório Detalhado")
    with st.spinner("Gerando relatório..."):
        time.sleep(2)
    exportar_excel_detalhado()
    st.success("Relatório gerado com sucesso!")
