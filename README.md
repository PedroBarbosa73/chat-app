# Chat Room Application

A modern, feature-rich chat application that allows users to create and participate in both public and private chat rooms. Built with Flask and Azure SQL Database.

## Features

- **User Authentication**
  - Secure user registration and login
  - Password hashing for user security
  - Session management

- **Chat Rooms**
  - Create public or private rooms
  - Password protection for private rooms
  - Real-time message updates
  - Room access management
  - Favorite rooms system

- **Messaging**
  - Real-time message display
  - Message pagination
  - Auto-scroll to new messages
  - Username display with messages
  - Timestamps for all messages

- **User Interface**
  - Modern, responsive design with Tailwind CSS
  - Three-panel layout (Favorites, Main Chat, Room Creation)
  - Active room highlighting
  - Room status indicators (Public/Private)
  - Clean and intuitive navigation

- **Security**
  - Secure password hashing
  - Protected API endpoints
  - Environment-based configuration
  - SQL injection prevention
  - XSS protection

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

## How to Use

1. Register for a new account or login with existing credentials
2. Create a new chat room (public or private)
3. Join existing rooms (enter password if required for private rooms)
4. Start chatting!
5. Favorite rooms you frequently visit
6. Use the three-panel interface to navigate between rooms

## Security Notes

1. Never commit your `.env` file to version control
2. Keep your secret key private and secure
3. Use environment variables for all sensitive information
4. Regularly rotate your database credentials and secret keys
5. Use strong, unique passwords for your database

## Production Recommendations

- Use strong secret keys
- Configure proper database settings
- Set up proper security measures
- Monitor application performance
- Set up proper backup procedures
- Use managed identities for database access
- Enable SSL/TLS encryption
- Implement rate limiting
- Set up logging and monitoring
- Configure automatic scaling 