# Message Exchange App

A simple web application that allows you to exchange messages with friends through unique URLs.

## Local Development Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the following structure:
```
SECRET_KEY=your-secret-key-here
AZURE_SQL_CONNECTIONSTRING=mssql+pyodbc://username:password@your-server.database.windows.net/your-database?driver=ODBC+Driver+18+for+SQL+Server
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
az sql server create --name your-server-name --resource-group myResourceGroup --location eastus

# Create SQL Database
az sql db create --resource-group myResourceGroup --server your-server-name --name your-database-name --edition Basic
```

3. Set up your environment variables in Azure App Service:
- Go to your App Service in Azure Portal
- Navigate to Settings > Configuration
- Add your SECRET_KEY and AZURE_SQL_CONNECTIONSTRING as new application settings
- Never commit these values to source control

4. Configure the firewall to allow Azure services:
```bash
az sql server firewall-rule create --resource-group myResourceGroup --server your-server-name --name AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
```

5. Deploy your application:
```bash
git add .
git commit -m "Ready for deployment"
git push azure main
```

## Security Notes

1. Never commit your `.env` file to version control
2. Keep your secret key private and secure
3. Use environment variables for all sensitive information
4. Regularly rotate your database credentials and secret keys
5. Use strong, unique passwords for your database

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