from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

app = Flask(__name__)

# Configuração do WebDriver
def iniciar_navegador():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Roda sem interface gráfica
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
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/section/div[2]/div[2]/div/div/div[2]/div/div/div/div/div[1]/div/input'))
        )
        campo_cpf.clear()
        campo_cpf.send_keys(cpf)

        botao_pesquisar = navegador.find_element(By.XPATH, '/html/body/div[1]/div[2]/section/div[2]/div[2]/div/div/div[2]/div/div/div/div/div[3]/div/div/input')
        botao_pesquisar.click()
        time.sleep(3)

        resultado = navegador.find_elements(By.XPATH, '/html/body/div[1]/div[2]/section/div[2]/div[2]/div/div/div[8]/div[2]/div/div/div/div/table/tbody/tr/td[1]/button')
        return "Usuário já cadastrado" if resultado else "Usuário não encontrado"
    except Exception as e:
        return {"error": "Erro ao buscar CPF", "detalhe": str(e)}

# Função para cadastrar um novo usuário
def cadastrar_usuario(navegador, dados):
    try:
        navegador.get("https://atendimento.sp.sebrae.com.br/Cadastro/Cliente/PessoaFisica")
        WebDriverWait(navegador, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="Nome"]'))
        ).send_keys(dados.get("nome", ""))

        navegador.find_element(By.XPATH, '//*[@id="CPF"]').send_keys(dados["cpf"])
        navegador.find_element(By.XPATH, '//*[@id="Celular"]').send_keys(dados["telefone"])
        navegador.find_element(By.XPATH, '//*[@id="DataNascimento"]').send_keys(dados["data_nascimento"])
        navegador.find_element(By.XPATH, '//*[@id="Email"]').send_keys(dados["email"])
        navegador.find_element(By.XPATH, '//*[@id="CEP"]').send_keys(dados["cep"])
        navegador.find_element(By.XPATH, '//*[@id="consultacep"]').click()
        time.sleep(2)
        navegador.find_element(By.XPATH, '//*[@id="EnderecoNumero"]').send_keys(dados["numero"])
        navegador.find_element(By.XPATH, '//*[@id="EnderecoComplemento"]').send_keys(dados["complemento"])

        # Selecionar o sexo com clique forçado via JavaScript
        try:
            genero = dados.get("genero", "").strip().lower()
            if genero == "masculino":
                elemento = WebDriverWait(navegador, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@name="Sexo" and @value="M"]'))
                )
                navegador.execute_script("arguments[0].click();", elemento)
                print("Sexo selecionado: Masculino")
            elif genero == "feminino":
                elemento = WebDriverWait(navegador, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@name="Sexo" and @value="F"]'))
                )
                navegador.execute_script("arguments[0].click();", elemento)
                print("Sexo selecionado: Feminino")
            else:
                print("Erro: Nenhum gênero válido informado. Cadastro pode falhar.")
        except Exception as e:
            print(f"Erro ao selecionar gênero: {e}")

        # Salvar cadastro
        navegador.find_element(By.XPATH, '/html/body/div[1]/div[2]/section/div[2]/div[1]/div/form/div[2]/div/div[2]/div[7]/div/button[3]').click()
        time.sleep(3)
        return {"status": "Cadastro realizado com sucesso"}
    except Exception as e:
        return {"error": "Erro no cadastro", "detalhe": str(e)}

# Endpoint para processar cadastros
@app.route('/processar', methods=['POST'])
def processar():
    dados = request.json
    if not dados or "cpf" not in dados:
        return jsonify({"error": "CPF obrigatório"}), 400

    navegador = iniciar_navegador()
    try:
        login(navegador)
        status = verificar_cadastro(navegador, dados["cpf"])
        if status == "Usuário já cadastrado":
            return jsonify({"status": "Usuário já cadastrado"})
        return jsonify(cadastrar_usuario(navegador, dados))
    finally:
        navegador.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
