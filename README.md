# Message Exchange App

A simple web application that allows you to exchange messages with friends through unique URLs.

## Local Development Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the following content:
```
SECRET_KEY=your-secret-key-here
AZURE_SQL_CONNECTIONSTRING=mssql+pyodbc://username:password@server.database.windows.net/database?driver=ODBC+Driver+18+for+SQL+Server
PORT=5000
```

3. Run the application:
```bash
python app.py
```

4. Open your web browser and go to `http://localhost:5000`

## Azure Deployment

### Prerequisites
- Azure account
- Azure CLI installed
- Git installed
- ODBC Driver 18 for SQL Server installed (for local development)

### Deployment Steps

1. Create a new Azure App Service:
```bash
az group create --name myResourceGroup --location eastus
az appservice plan create --name myAppServicePlan --resource-group myResourceGroup --sku B1 --is-linux
az webapp create --resource-group myResourceGroup --plan myAppServicePlan --name your-app-name --runtime "PYTHON|3.9"
```

2. Create an Azure SQL Database:
```bash
# Create SQL Server
az sql server create --name your-server-name --resource-group myResourceGroup --location eastus --admin-user your-admin --admin-password your-password

# Create SQL Database
az sql db create --resource-group myResourceGroup --server your-server-name --name your-database-name --edition Basic --capacity 5
```

3. Get the connection string:
```bash
# Get the connection string
az sql db show-connection-string --client sqlcmd --server your-server-name --name your-database-name
```

4. Set the environment variables in Azure:
```bash
az webapp config appsettings set --resource-group myResourceGroup --name your-app-name --settings \
    SECRET_KEY="your-secret-key" \
    AZURE_SQL_CONNECTIONSTRING="your-connection-string"
```

5. Configure the firewall to allow Azure services:
```bash
az sql server firewall-rule create --resource-group myResourceGroup --server your-server-name --name AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
```

6. Deploy your application:
```bash
git add .
git commit -m "Ready for Azure deployment"
git push azure main
```

## How to Use

1. Type your message in the text area
2. Click "Create Message Link"
3. Share the generated URL with your friend
4. Your friend can view the message by opening the URL

## Features

- Simple and clean interface
- Secure message sharing through unique URLs
- No registration required
- Cloud deployment ready
- Azure SQL Database support

## Note

For production use, make sure to:
- Use strong secret keys
- Configure proper database settings
- Set up proper security measures
- Monitor application performance
- Set up proper backup procedures
- Use managed identities for database access (recommended for production) 