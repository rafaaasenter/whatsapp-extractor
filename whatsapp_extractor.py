from flask import Flask, render_template_string, jsonify, request, send_file
import os
import time
import base64
import logging
import csv
import json
from datetime import datetime
from io import BytesIO
import qrcode
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Variáveis globais
driver = None
qr_code_image = None
connected = False
contacts = []

# Template HTML
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Extrator de Contatos WhatsApp</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #075e54;
            text-align: center;
        }
        .container {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .btn {
            background-color: #128c7e;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin: 5px;
        }
        .btn:hover {
            background-color: #075e54;
        }
        .btn:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        .qr-container {
            display: flex;
            justify-content: center;
            margin: 20px 0;
        }
        .qr-code {
            width: 250px;
            height: 250px;
        }
        .status {
            text-align: center;
            margin: 15px 0;
            font-weight: bold;
        }
        .contact-list {
            margin-top: 20px;
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 4px;
        }
        .contact-item {
            padding: 8px;
            border-bottom: 1px solid #eee;
        }
        .contact-item:last-child {
            border-bottom: none;
        }
        .export-options {
            margin-top: 15px;
            display: flex;
            justify-content: center;
        }
        .export-btn {
            background-color: #34b7f1;
        }
        .export-btn:hover {
            background-color: #0f9bd7;
        }
        .hidden {
            display: none;
        }
        .progress-container {
            width: 100%;
            background-color: #f3f3f3;
            border-radius: 4px;
            margin: 10px 0;
        }
        .progress-bar {
            height: 20px;
            background-color: #128c7e;
            border-radius: 4px;
            text-align: center;
            color: white;
            line-height: 20px;
        }
        .alert {
            padding: 10px;
            background-color: #f44336;
            color: white;
            margin: 10px 0;
            border-radius: 4px;
        }
        .instructions {
            background-color: #e7f3ef;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .instructions ol {
            margin-left: 20px;
            padding-left: 0;
        }
        .instructions li {
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <h1>Extrator de Contatos WhatsApp</h1>
    
    <div class="container">
        <div class="instructions">
            <h3>Instruções:</h3>
            <ol>
                <li>Clique em "Conectar ao WhatsApp" para gerar o código QR.</li>
                <li>Escaneie o código QR com seu telefone (WhatsApp > Menu > WhatsApp Web).</li>
                <li>Após conectar, clique em "Extrair Contatos" para iniciar a extração.</li>
                <li>Quando a extração for concluída, você poderá exportar os contatos nos formatos disponíveis.</li>
            </ol>
        </div>
        
        <div class="controls">
            <button id="connect-btn" class="btn">Conectar ao WhatsApp</button>
            <button id="extract-btn" class="btn" disabled>Extrair Contatos</button>
        </div>
        
        <div class="status" id="status">Aguardando conexão...</div>
        
        <div class="qr-container hidden" id="qr-container">
            <img id="qr-code" class="qr-code">
        </div>
        
        <div class="progress-container hidden" id="progress-container">
            <div class="progress-bar" id="progress-bar" style="width: 0%">0%</div>
        </div>
        
        <div id="error-container" class="alert hidden"></div>
        
        <div class="contact-list hidden" id="contact-list">
            <!-- Os contatos serão inseridos aqui via JavaScript -->
        </div>
        
        <div class="export-options hidden" id="export-options">
            <button class="btn export-btn" data-format="csv">Exportar CSV</button>
            <button class="btn export-btn" data-format="json">Exportar JSON</button>
            <button class="btn export-btn" data-format="txt">Exportar TXT</button>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const connectBtn = document.getElementById('connect-btn');
            const extractBtn = document.getElementById('extract-btn');
            const statusEl = document.getElementById('status');
            const qrContainer = document.getElementById('qr-container');
            const qrCode = document.getElementById('qr-code');
            const contactList = document.getElementById('contact-list');
            const exportOptions = document.getElementById('export-options');
            const progressContainer = document.getElementById('progress-container');
            const progressBar = document.getElementById('progress-bar');
            const errorContainer = document.getElementById('error-container');
            
            let statusCheckInterval;
            let contacts = [];
            
            // Conectar ao WhatsApp
            connectBtn.addEventListener('click', async function() {
                try {
                    statusEl.textContent = 'Iniciando conexão...';
                    const response = await fetch('/api/connect', {
                        method: 'POST'
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        // Mostrar código QR
                        getQRCode();
                        
                        // Verificar status de conexão
                        statusCheckInterval = setInterval(checkStatus, 5000);
                    } else {
                        showError(data.message || 'Erro ao conectar');
                    }
                } catch (error) {
                    showError('Erro ao conectar: ' + error.message);
                }
            });
            
            // Obter código QR
            async function getQRCode() {
                try {
                    const response = await fetch('/api/qr');
                    const data = await response.json();
                    
                    if (data.qr_code) {
                        qrCode.src = `data:image/png;base64,${data.qr_code}`;
                        qrContainer.classList.remove('hidden');
                    } else {
                        showError('QR Code não disponível');
                    }
                } catch (error) {
                    showError('Erro ao obter QR code: ' + error.message);
                }
            }
            
            // Verificar status da conexão
            async function checkStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    
                    statusEl.textContent = data.status;
                    
                    if (data.status === 'Conectado') {
                        clearInterval(statusCheckInterval);
                        extractBtn.disabled = false;
                    }
                } catch (error) {
                    showError('Erro ao verificar status: ' + error.message);
                }
            }
            
            // Extrair contatos
            extractBtn.addEventListener('click', async function() {
                try {
                    statusEl.textContent = 'Extraindo contatos...';
                    progressContainer.classList.remove('hidden');
                    updateProgress(10);
                    
                    const response = await fetch('/api/extract', {
                        method: 'POST'
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        contacts = data.contacts;
                        updateProgress(100);
                        
                        // Exibir contatos
                        contactList.innerHTML = '';
                        contacts.forEach(contact => {
                            const contactElement = document.createElement('div');
                            contactElement.className = 'contact-item';
                            contactElement.textContent = `${contact.name}: ${contact.phone}`;
                            contactList.appendChild(contactElement);
                        });
                        
                        contactList.classList.remove('hidden');
                        exportOptions.classList.remove('hidden');
                        statusEl.textContent = `Extração concluída! ${contacts.length} contatos encontrados.`;
                    } else {
                        showError(data.message || 'Erro ao extrair contatos');
                    }
                } catch (error) {
                    showError('Erro ao extrair contatos: ' + error.message);
                }
            });
            
            // Exportar contatos
            document.querySelectorAll('.export-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const format = this.dataset.format;
                    window.location.href = `/api/export/${format}`;
                });
            });
            
            // Atualizar barra de progresso
            function updateProgress(percentage) {
                progressBar.style.width = `${percentage}%`;
                progressBar.textContent = `${percentage}%`;
            }
            
            // Exibir mensagem de erro
            function showError(message) {
                errorContainer.textContent = message;
                errorContainer.classList.remove('hidden');
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/connect', methods=['POST'])
def connect_whatsapp():
    global driver, qr_code_image, connected
    
    try:
        # Configurar o Chrome em modo headless
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Iniciar o Chrome com ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Abrir WhatsApp Web
        driver.get("https://web.whatsapp.com/")
        logger.info("Iniciando WhatsApp Web")
        
        # Esperar pela página carregar e QR code aparecer
        qr_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//canvas[contains(@aria-label, 'Scan me!')]"))
        )
        
        # Extrair imagem do QR code
        canvas = driver.execute_script("return document.querySelector('canvas[aria-label*=\"Scan me!\"]')")
        qr_data_url = driver.execute_script("return arguments[0].toDataURL('image/png').substring(22);", canvas)
        qr_code_image = qr_data_url
        
        return jsonify({"success": True, "message": "QR Code gerado com sucesso"})
    except Exception as e:
        logger.error(f"Erro ao conectar: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/qr')
def get_qr_code():
    global qr_code_image
    
    if qr_code_image:
        return jsonify({"qr_code": qr_code_image})
    else:
        return jsonify({"error": "QR Code não disponível"}), 404

@app.route('/api/status')
def get_status():
    global driver, connected
    
    try:
        if not driver:
            return jsonify({"status": "Não conectado"})
        
        # Verificar se a página principal do WhatsApp foi carregada (pós-login)
        try:
            side_pane = driver.find_element(By.XPATH, "//div[@id='pane-side']")
            connected = True
            return jsonify({"status": "Conectado"})
        except:
            # Verificar se ainda está na tela de QR code
            try:
                qr_code = driver.find_element(By.XPATH, "//canvas[contains(@aria-label, 'Scan me!')]")
                return jsonify({"status": "Aguardando escaneamento do QR Code"})
            except:
                # Verificando se está carregando
                return jsonify({"status": "Conectando..."})
    except Exception as e:
        logger.error(f"Erro ao verificar status: {str(e)}")
        return jsonify({"status": "Erro: " + str(e)})

@app.route('/api/extract', methods=['POST'])
def extract_contacts():
    global driver, contacts
    
    if not driver or not connected:
        return jsonify({"success": False, "message": "Não conectado ao WhatsApp"})
    
    try:
        logger.info("Iniciando extração de contatos")
        extracted_contacts = []
        
        # Clicar no botão de novo chat
        new_chat_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@title='New chat' or @title='Novo chat']"))
        )
        new_chat_button.click()
        logger.info("Botão de novo chat clicado")
        
        time.sleep(2)  # Esperar o painel de contatos carregar
        
        # Extrair contatos da lista
        contact_elements = driver.find_elements(By.XPATH, "//div[contains(@class, '_3OvU8')]") # Ajuste esse seletor conforme necessário
        logger.info(f"Encontrados {len(contact_elements)} elementos de contato")
        
        for element in contact_elements:
            try:
                name_element = element.find_element(By.XPATH, ".//span[contains(@class, 'ggj6brxn')]") # Ajuste esse seletor
                name = name_element.text.strip()
                
                # Obter número de telefone (pode exigir clicar no contato e extrair detalhes)
                # Esta é uma versão simplificada - em uma implementação real, 
                # você precisaria clicar em cada contato para obter o número
                phone = "Não disponível"  # WhatsApp nem sempre exibe o número diretamente
                
                if name and name != "":
                    extracted_contacts.append({"name": name, "phone": phone})
            except Exception as inner_e:
                logger.warning(f"Erro ao extrair um contato: {str(inner_e)}")
        
        # Fechar a janela de novo chat (clicando no botão de voltar)
        try:
            back_button = driver.find_element(By.XPATH, "//span[@data-icon='back' or @data-icon='x-viewer']")
            back_button.click()
        except:
            logger.warning("Não foi possível fechar a janela de novo chat")
        
        contacts = extracted_contacts
        logger.info(f"Extração concluída. {len(contacts)} contatos encontrados.")
        
        return jsonify({"success": True, "contacts": contacts})
    except Exception as e:
        logger.error(f"Erro ao extrair contatos: {str(e)}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/export/<format>')
def export_contacts(format):
    global contacts
    
    if not contacts:
        return jsonify({"error": "Nenhum contato disponível para exportação"}), 400
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Garantir que a pasta exports existe
        if not os.path.exists('exports'):
            os.makedirs('exports')
            
        if format == 'csv':
            # Exportar como CSV
            filename = f"exports/contatos_whatsapp_{timestamp}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=['name', 'phone'])
                writer.writeheader()
                writer.writerows(contacts)
            
            return send_file(filename, as_attachment=True)
        
        elif format == 'json':
            # Exportar como JSON
            filename = f"exports/contatos_whatsapp_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(contacts, jsonfile, ensure_ascii=False, indent=2)
            
            return send_file(filename, as_attachment=True)
        
        elif format == 'txt':
            # Exportar como TXT
            filename = f"exports/contatos_whatsapp_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as txtfile:
                txtfile.write("CONTATOS WHATSAPP\n\n")
                for contact in contacts:
                    txtfile.write(f"Nome: {contact['name']}\n")
                    txtfile.write(f"Telefone: {contact['phone']}\n")
                    txtfile.write("-" * 30 + "\n")
            
            return send_file(filename, as_attachment=True)
        
        else:
            return jsonify({"error": "Formato não suportado"}), 400
    
    except Exception as e:
        logger.error(f"Erro ao exportar contatos: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Os arquivos exportados serão salvos na pasta exports
    if not os.path.exists('exports'):
        os.makedirs('exports')
        
    app.run(host='0.0.0.0', port=5000, debug=True)