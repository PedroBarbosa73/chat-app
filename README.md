# Message Exchange App

A simple web application that allows you to exchange messages with friends through unique URLs.

## Local Development Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file:
   - Copy `.env.example` to `.env`
   - Fill in your environment variables
   - NEVER commit the `.env` file to version control

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

3. Configure environment variables in Azure:
   - Use Azure Portal or Azure CLI to set application settings
   - NEVER store credentials in code or version control
   - Use Azure Key Vault for production environments

4. Configure the firewall to allow Azure services:
```bash
az sql server firewall-rule create --resource-group myResourceGroup --server your-server-name --name AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
```

5. Deploy your application:
```bash
git add .
git commit -m "Ready for Azure deployment"
git push azure main
```

## Security Best Practices

1. **Environment Variables**
   - Use environment variables for all sensitive information
   - Never commit `.env` files to version control
   - Use different credentials for development and production

2. **Database Security**
   - Use managed identities for database access in production
   - Regularly rotate database credentials
   - Enable Azure SQL Database threat detection
   - Use SSL/TLS for all database connections

3. **Application Security**
   - Use strong, randomly generated secret keys
   - Enable HTTPS in production
   - Implement proper input validation
   - Use parameterized queries for database operations

4. **Azure Security**
   - Use Azure Key Vault for secrets management
   - Implement proper RBAC (Role-Based Access Control)
   - Enable Azure Security Center
   - Set up monitoring and alerts

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