# Extrator de Contatos do WhatsApp

Esta ferramenta permite extrair seus contatos do WhatsApp Web e exportá-los em diferentes formatos (CSV, JSON, TXT).

## Instalação com Docker (Recomendado)

### Pré-requisitos

- Docker instalado em sua VPS (servidor)
- Docker Compose instalado em sua VPS

### Passos para Instalação

1. Crie uma pasta para o projeto:

```bash
mkdir -p /root/whatsapp-extractor
cd /root/whatsapp-extractor
```

2. Copie todos os arquivos deste pacote para a pasta criada (você pode usar SFTP, SCP ou outro método para transferir os arquivos).

3. Crie a pasta para os arquivos exportados:

```bash
mkdir -p exports
```

4. Construa e inicie o container Docker:

```bash
docker-compose up -d
```

5. Acesse a aplicação no navegador:
   - URL: `http://seu_ip_ou_dominio:8336`

## Como Usar

1. Acesse a aplicação no navegador.
2. Clique em "Conectar ao WhatsApp".
3. Escaneie o código QR exibido usando seu celular:
   - Abra o WhatsApp no celular
   - Vá em Menu (três pontos) > WhatsApp Web
   - Escaneie o QR code exibido na tela
4. Após a conexão, clique em "Extrair Contatos".
5. Quando a extração for concluída, você verá seus contatos listados.
6. Use os botões de exportação para baixar seus contatos no formato desejado (CSV, JSON ou TXT).

## Arquivos Importantes

- `whatsapp_extractor.py`: O script principal
- `Dockerfile`: Configuração para construir a imagem Docker
- `docker-compose.yml`: Configuração para executar o container
- `requirements.txt`: Dependências do Python

## Possíveis Problemas e Soluções

### O container não inicia

Verifique os logs do container:

```bash
docker-compose logs
```

### O QR code não aparece

Verifique os logs e reinicie o container:

```bash
docker-compose restart
```

### Não consigo escanear o QR code

Certifique-se de que seu celular está com o WhatsApp atualizado e tente novamente.

### A extração não funciona

O WhatsApp Web pode mudar seus seletores CSS/XPath. Caso encontre problemas, verifique se há atualizações disponíveis para esta ferramenta.

## Manutenção

Para atualizar ou reiniciar a aplicação:

```bash
# Parar o container
docker-compose down

# Reconstruir e iniciar
docker-compose up -d --build
```

## Observações de Segurança

- Esta ferramenta acessa seu WhatsApp Web, por isso deve ser instalada apenas em servidores seguros.
- Proteja o acesso à URL da aplicação (idealmente use HTTPS e alguma forma de autenticação).
- Não compartilhe o acesso à aplicação com pessoas não autorizadas.