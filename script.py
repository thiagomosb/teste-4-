import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Defina sua chave da API
API_KEY = "16f8bf0f703c8d8555393df29be231c3"

# Lista de cidades para o filtro
cidades_disponiveis = ["Morrinhos", "Itumbiara", "Pires do Rio", "Catalão", "Caldas Novas"]

# Filtro de cidades
cidades_selecionadas = st.multiselect("Selecione as cidades", cidades_disponiveis, default=cidades_disponiveis)

# Filtro de risco de chuva
risco_filtro = st.radio("Filtrar por Risco de Chuva", ("Ambos", "Risco de Chuva", "Sem Risco de Chuva"))


# Função para obter o clima atual de uma cidade
def obter_clima(cidade):
    clima_atual_link = f"https://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={API_KEY}&lang=pt_br"
    requisicao_clima = requests.get(clima_atual_link)

    if requisicao_clima.status_code == 200:
        return requisicao_clima.json()
    else:
        return None


# Função para obter a previsão para os próximos dias
def obter_previsao(cidade):
    previsao_link = f"https://api.openweathermap.org/data/2.5/forecast?q={cidade}&appid={API_KEY}&lang=pt_br"
    requisicao_previsao = requests.get(previsao_link)

    if requisicao_previsao.status_code == 200:
        return requisicao_previsao.json()
    else:
        return None


# Função para formatar a data no padrão brasileiro (dd/mm/aaaa)
def formatar_data(data):
    return data.strftime("%d/%m/%Y")  # Formato: dia/mês/ano


# Função para plotar o gráfico de temperatura com pontos de risco de chuva em vermelho e verde
def plotar_grafico_temperatura(previsao_data, risco_filtro):
    # Lista para armazenar as horas, temperaturas e cores para o gráfico
    horas = []
    temperaturas = []
    cores = []  # Para armazenar as cores dos pontos (vermelho ou verde)

    # Loop para extrair a previsão de temperatura a cada 3 horas
    for previsao in previsao_data['list']:
        hora = datetime.fromtimestamp(previsao['dt'], tz=timezone.utc)
        temperatura = previsao['main']['temp'] - 273.15  # Convertendo de Kelvin para Celsius
        chuva = previsao.get('rain', {}).get('3h', 0)  # Chuva nas últimas 3 horas (em mm)

        # Se houver chuva significativa, o ponto será vermelho (risco de chuva)
        if chuva > 1.0:
            cores.append('red')
        else:
            cores.append('green')

        # Armazenando dados
        horas.append(hora.strftime("%H:%M"))
        temperaturas.append(temperatura)

    # Filtrar os pontos conforme o risco de chuva selecionado
    if risco_filtro == "Risco de Chuva":
        cores = ['red' if cor == 'red' else 'white' for cor in cores]  # Manter apenas os pontos vermelhos
    elif risco_filtro == "Sem Risco de Chuva":
        cores = ['green' if cor == 'green' else 'white' for cor in cores]  # Manter apenas os pontos verdes

    # Plotando o gráfico
    plt.figure(figsize=(10, 5))

    # Plotando os pontos com cores diferentes (vermelho ou verde)
    for i in range(len(horas)):
        if cores[i] != 'white':  # Excluir os pontos "brancos" (não visíveis)
            plt.scatter(horas[i], temperaturas[i], color=cores[i],
                        label='Risco de Chuva' if cores[i] == 'red' else 'Sem Risco')

    plt.plot(horas, temperaturas, color='blue', label='Temperatura (°C)', alpha=0.5)  # Linha azul para a temperatura
    plt.title('Previsão de Temperatura nas Próximas Horas')
    plt.xlabel('Hora')
    plt.ylabel('Temperatura (°C)')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.legend()

    # Exibindo o gráfico
    st.pyplot(plt)


# Função para gerar o gráfico de Risco de Chuva por Dia (apontando dias com risco)
def plotar_grafico_risco_chuva(previsao_data):
    dias = []
    horas_risco = []
    risco_por_dia = {}

    # Loop para extrair as previsões dos próximos dias
    for previsao in previsao_data['list']:
        hora = datetime.fromtimestamp(previsao['dt'], tz=timezone.utc)
        data = hora.date()

        chuva = previsao.get('rain', {}).get('3h', 0)  # Chuva nas últimas 3 horas (em mm)

        # Se houver risco de chuva (mais que 1 mm), armazenamos a hora e o dia
        if chuva > 1.0:
            if data not in risco_por_dia:
                risco_por_dia[data] = []
            risco_por_dia[data].append(hora.strftime("%H:%M"))

    # Preparando os dados para o gráfico
    for dia, horas in risco_por_dia.items():
        dias.append(formatar_data(dia))  # Formatar a data para o formato brasileiro
        horas_risco.append(len(horas))  # Contando as horas com risco de chuva por dia

    # Plotando o gráfico
    plt.figure(figsize=(10, 5))
    plt.bar(dias, horas_risco, color='red', label='Risco de Chuva')
    plt.title('Risco de Chuva nos Próximos Dias')
    plt.xlabel('Dia')
    plt.ylabel('Número de Horários com Risco de Chuva')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()

    # Exibindo o gráfico
    st.pyplot(plt)

    return risco_por_dia  # Retornando os dados para a tabela


# Função para gerar a tabela com os indicadores de previsão por horários
def gerar_tabela_risco(previsao_data, risco_filtro):
    dados = []

    # Loop para extrair a previsão de temperatura e risco de chuva
    for previsao in previsao_data['list']:
        hora = datetime.fromtimestamp(previsao['dt'], tz=timezone.utc)
        temperatura = previsao['main']['temp'] - 273.15  # Convertendo de Kelvin para Celsius
        chuva = previsao.get('rain', {}).get('3h', 0)  # Chuva nas últimas 3 horas (em mm)

        # Determinando o risco de chuva
        if chuva > 1.0:
            risco = "Risco de Chuva"
        else:
            risco = "Sem Risco"

        # Adicionando as informações à lista de dados
        dados.append([hora.strftime("%H:%M"), temperatura, chuva, risco])

    # Convertendo para DataFrame do pandas
    tabela = pd.DataFrame(dados, columns=["Hora", "Temperatura (°C)", "Precipitação (mm)", "Risco de Chuva"])

    # Filtrando a tabela conforme o risco de chuva selecionado
    if risco_filtro == "Risco de Chuva":
        tabela = tabela[tabela["Risco de Chuva"] == "Risco de Chuva"]
    elif risco_filtro == "Sem Risco de Chuva":
        tabela = tabela[tabela["Risco de Chuva"] == "Sem Risco"]

    # Exibindo a tabela no Streamlit
    st.table(tabela)


# Função para gerar a tabela de risco de chuva por dia (para o gráfico de risco de chuva)
def gerar_tabela_risco_dia(risco_por_dia):
    # Convertendo os dados para um DataFrame
    tabela_risco = pd.DataFrame(list(risco_por_dia.items()), columns=["Dia", "Horas com Risco de Chuva"])
    tabela_risco["Dia"] = pd.to_datetime(tabela_risco["Dia"])
    tabela_risco["Dia"] = tabela_risco["Dia"].dt.strftime("%d/%m/%Y")  # Formatando a data para o formato brasileiro
    tabela_risco = tabela_risco.sort_values(by="Dia")

    # Exibindo a tabela no Streamlit
    st.table(tabela_risco)


# Função para verificar o risco de chuva e exibir a mensagem apropriada
def verificar_risco_chuva(previsao_data):
    maior_chuva = 0
    hora_risco = None

    for previsao in previsao_data['list']:
        chuva = previsao.get('rain', {}).get('3h', 0)  # Chuva nas últimas 3 horas (em mm)
        if chuva > maior_chuva:
            maior_chuva = chuva
            hora_risco = datetime.fromtimestamp(previsao['dt'], tz=timezone.utc)

    # Se houver risco de chuva, exibe a mensagem de risco
    if maior_chuva > 1.0:  # Se a chuva for maior que 1mm, consideramos risco
        return f"Risco de Chuva, Afetando o Planejamento das Equipes. Previsão de {maior_chuva} mm de chuva às {hora_risco.strftime('%H:%M')}"
    else:
        return "Sem risco no Planejamento"


# Loop para percorrer as cidades selecionadas e mostrar as informações no Streamlit
for cidade in cidades_selecionadas:
    st.title(f"Clima em {cidade.capitalize()}")

    # Obter dados do clima atual
    clima_data = obter_clima(cidade)

    if clima_data:
        descricao = clima_data['weather'][0]['description']
        temperatura = clima_data['main']['temp'] - 273.15  # Convertendo de Kelvin para Celsius
        chuva_percentual = clima_data.get('rain', {}).get('1h',
                                                          0)  # Usando '1h' para a quantidade de chuva nas últimas 1h

        # Mostrar clima atual
        st.write(f"**Descrição:** {descricao}")
        st.write(f"**Temperatura:** {temperatura:.2f}°C")
        st.write(f"**Chuva nas últimas 1h:** {chuva_percentual} mm")
    else:
        st.error(f"Erro ao obter os dados do clima para {cidade.capitalize()}.")

    # Obter previsão para os próximos dias
    previsao_data = obter_previsao(cidade)

    if previsao_data:
        previsao_dia_seguinte = None
        for previsao in previsao_data['list']:
            data_previsao = datetime.fromtimestamp(previsao['dt'], tz=timezone.utc)
            if data_previsao >= datetime.now(timezone.utc) + timedelta(
                    days=1):  # Garantindo previsão para o próximo dia
                previsao_dia_seguinte = previsao
                break

        if previsao_dia_seguinte:
            descricao_previsao = previsao_dia_seguinte['weather'][0]['description']
            temperatura_previsao = previsao_dia_seguinte['main']['temp'] - 273.15  # Convertendo para Celsius
            st.write(f"\n**Previsão para o Próximo Dia:**")
            st.write(f"**Descrição:** {descricao_previsao}")
            st.write(f"**Temperatura:** {temperatura_previsao:.2f}°C")
        else:
            st.warning(f"Não foi possível encontrar a previsão para o próximo dia em {cidade.capitalize()}.")

        # Exibindo risco de chuva
        mensagem_risco_chuva = verificar_risco_chuva(previsao_data)

        # Mostrar a mensagem de risco de chuva
        st.write(f"**Estado de Chuva:** {mensagem_risco_chuva}")

        # Plotando o gráfico de temperatura com os pontos coloridos
        plotar_grafico_temperatura(previsao_data, risco_filtro)

        # Gerando a tabela de previsão de risco de chuva
        gerar_tabela_risco(previsao_data, risco_filtro)

        # Gerando gráfico de risco de chuva para os próximos dias
        risco_por_dia = plotar_grafico_risco_chuva(previsao_data)

        # Gerando a tabela de risco de chuva por dia
        gerar_tabela_risco_dia(risco_por_dia)
    else:
        st.error(f"Erro ao obter a previsão para {cidade.capitalize()}.")

    st.write("---")  # Separador entre cidades
