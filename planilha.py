import pandas as pd
import os
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Nome do arquivo CSV (salvo na mesma pasta do projeto)
arquivo_csv = r"C:\Users\maico\Documents\VS Code\python\Script RAE\dados_processados.csv"

# Verifica se o arquivo existe antes de tentar carregar
if not os.path.exists(arquivo_csv):
    raise FileNotFoundError(f"Arquivo {arquivo_csv} não encontrado!")

# Função para limpar caracteres não numéricos
def limpar_numeros(texto):
    return re.sub(r'\D', '', str(texto)) if texto else ""

# Carregar o CSV no DataFrame, garantindo que os CPFs, telefones e CEPs sejam strings
df = pd.read_csv(arquivo_csv, dtype=str)

# Filtrar os cadastros com status "Pronto para envio"
df = df[df["status"] == "Pronto para envio"]

# Configuração do WebDriver
def iniciar_navegador():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# Função para fazer login no sistema
def login(navegador):
    navegador.get("https://atendimento.sp.sebrae.com.br/Home")
    try:
        email_input = WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/section/div[3]/div/div[1]/div/form/div[1]/input'))
        )
        email_input.send_keys("p_julielfna")

        senha_input = navegador.find_element(By.XPATH, '/html/body/section/div[3]/div/div[1]/div/form/div[2]/input')
        senha_input.send_keys("Sebrae@1702@")

        login_button = navegador.find_element(By.XPATH, '/html/body/section/div[3]/div/div[1]/div/form/div[3]/div[2]/input')
        login_button.click()
        time.sleep(3)
    except Exception as e:
        return {"error": "Falha no login", "detalhe": str(e)}

# Função para verificar se o CPF já está cadastrado
def verificar_cadastro(navegador, cpf):
    navegador.get("https://atendimento.sp.sebrae.com.br/Cadastro/Cliente")
    try:
        campo_cpf = WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="CPF"]'))
        )
        campo_cpf.clear()
        campo_cpf.send_keys(cpf)

        botao_pesquisar = navegador.find_element(By.XPATH, '/html/body/div[1]/div[2]/section/div[2]/div[2]/div/div/div[2]/div/div/div/div/div[3]/div/div/input')
        botao_pesquisar.click()
        time.sleep(3)

        resultado = navegador.find_elements(By.XPATH, '/html/body/div[1]/div[2]/section/div[2]/div[2]/div/div/div[8]/div[2]/div/div/div/div/table/tbody/tr/td[1]/button')
        return "Usuário já cadastrado" if resultado else "Usuário não encontrado"
    except Exception as e:
        return f"Erro ao buscar CPF: {str(e)}"

# Função para cadastrar um novo usuário
def cadastrar_usuario(navegador, dados):
    try:
        navegador.get("https://atendimento.sp.sebrae.com.br/Cadastro/Cliente/PessoaFisica")

        # Limpar os dados antes de preencher
        cpf = limpar_numeros(dados.get("cpf", ""))
        telefone = limpar_numeros(dados.get("telefone", ""))
        cep = limpar_numeros(dados.get("cep", ""))

        WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="Nome"]'))
        ).send_keys(dados.get("nome", ""))

        navegador.find_element(By.XPATH, '//*[@id="CPF"]').send_keys(cpf)
        navegador.find_element(By.XPATH, '//*[@id="DataNascimento"]').send_keys(dados.get("data_nascimento", ""))
        navegador.find_element(By.XPATH, '//*[@id="Email"]').send_keys(dados.get("email", ""))
        navegador.find_element(By.XPATH, '//*[@id="Celular"]').send_keys(telefone)
        navegador.find_element(By.XPATH, '//*[@id="CEP"]').send_keys(cep)
        navegador.find_element(By.XPATH, '//*[@id="consultacep"]').click()
        time.sleep(2)
        navegador.find_element(By.XPATH, '//*[@id="EnderecoNumero"]').send_keys(dados.get("numero", ""))
        navegador.find_element(By.XPATH, '//*[@id="EnderecoComplemento"]').send_keys(dados.get("complemento", ""))

        # Selecionar o sexo com clique forçado via JavaScript
        try:
            genero = dados.get("genero", "").strip().lower()
            if genero == "masculino":
                elemento = WebDriverWait(navegador, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@name="Sexo" and @value="M"]'))
                )
                navegador.execute_script("arguments[0].click();", elemento)
            elif genero == "feminino":
                elemento = WebDriverWait(navegador, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@name="Sexo" and @value="F"]'))
                )
                navegador.execute_script("arguments[0].click();", elemento)

        except Exception as e:
            print(f"Erro ao selecionar gênero: {e}")

        # Salvar cadastro
        navegador.find_element(By.XPATH, '/html/body/div[1]/div[2]/section/div[2]/div[1]/div/form/div[2]/div/div[2]/div[7]/div/button[3]').click()
        time.sleep(3)
        return "Cadastro realizado com sucesso"
    except Exception as e:
        return f"Erro no cadastro: {str(e)}"

# Iniciar navegador
navegador = iniciar_navegador()
login(navegador)

# Processar cada linha da planilha
for index, row in df.iterrows():
    cpf = limpar_numeros(row["cpf"])

    # Verificar se CPF já está cadastrado
    status = verificar_cadastro(navegador, cpf)

    if status == "Usuário já cadastrado":
        df.at[index, "status"] = "Usuário já cadastrado"
    else:
        resultado = cadastrar_usuario(navegador, row.to_dict())
        df.at[index, "status"] = resultado

# Fechar navegador
navegador.quit()

# Salvar planilha atualizada
df.to_csv(arquivo_csv, index=False)
print("Processo concluído e planilha atualizada.")
