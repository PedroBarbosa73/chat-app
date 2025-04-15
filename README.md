# Chat Room Application

A modern, feature-rich chat application that allows users to create and participate in both public and private chat rooms. Built with Flask and Azure cloud services.

## Features

- **User Authentication**
  - Secure user registration and login
  - Password hashing for user security
  - Persistent session management
  - Remember me functionality

- **Chat Rooms**
  - Create public or private rooms
  - Password protection for private rooms
  - Real-time message updates
  - Room access management
  - Enhanced favorites system with dropdown navigation
  - Quick room switching via favorites menu

- **Messaging**
  - Real-time message display
  - Message pagination with infinite scroll
  - Auto-scroll to new messages
  - Username display with messages
  - Timestamps for all messages
  - Media support (images and videos)
  - File upload progress indicators
  - Image lightbox for fullscreen viewing

- **Media Features**
  - Support for image uploads (JPEG, PNG, GIF)
  - Video file support
  - Secure file storage using Azure Blob Storage
  - Image preview in chat
  - Lightbox for fullscreen image viewing
  - Upload progress indicators
  - Secure URL generation for media access

- **User Interface**
  - Modern, responsive design with Tailwind CSS
  - Three-panel layout (Favorites, Main Chat, Room Creation)
  - Active room highlighting
  - Room status indicators (Public/Private)
  - Clean and intuitive navigation
  - Favorites dropdown for quick room access
  - Loading indicators for all operations
  - Improved mobile responsiveness

- **Security**
  - Secure password hashing
  - Protected API endpoints
  - Environment-based configuration
  - SQL injection prevention
  - XSS protection
  - Secure media file handling
  - Azure Blob Storage security

## Local Development Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the following structure:
```
SECRET_KEY=your-secret-key-here
AZURE_SQL_CONNECTIONSTRING=mssql+pyodbc://username:password@your-server.database.windows.net/your-database?driver=ODBC+Driver+18+for+SQL+Server
AZURE_STORAGE_CONNECTION_STRING=your-azure-storage-connection-string
PORT=8000
```

3. Run the application:
```bash
python app.py
```

4. Open your web browser and go to `http://localhost:8000`

## Azure Deployment

### Prerequisites
- Azure account
- Azure CLI installed
- Git installed
- ODBC Driver 18 for SQL Server installed (for local development)
- Azure Storage Account for media files

### Required Azure Services
1. Azure App Service (for hosting)
2. Azure SQL Database (for data storage)
3. Azure Blob Storage (for media files)

### Deployment Steps

1. Create required Azure services:
   - App Service
   - SQL Database
   - Storage Account for media

2. Configure environment variables in Azure App Service:
   - SECRET_KEY
   - AZURE_SQL_CONNECTIONSTRING
   - AZURE_STORAGE_CONNECTION_STRING

3. Deploy using GitHub Actions:
   - Automatic deployment on push to main branch
   - Python 3.9 runtime
   - Production-ready configuration

## How to Use

1. Register for a new account or login with existing credentials
2. Create a new chat room (public or private)
3. Join existing rooms (enter password if required for private rooms)
4. Start chatting!
5. Share images and videos:
   - Click the upload button
   - Select your media file
   - Wait for upload to complete
   - Media will appear in the chat
6. Manage favorite rooms:
   - Click the star icon to favorite a room
   - Use the favorites dropdown for quick access
   - Switch between rooms easily
7. View images:
   - Click on images to view in fullscreen
   - Use the lightbox navigation
   - Close with escape key or click outside

## Security Notes

1. Never commit your `.env` file to version control
2. Keep your secret key private and secure
3. Use environment variables for all sensitive information
4. Regularly rotate your database credentials and secret keys
5. Use strong, unique passwords for your database
6. Secure your Azure Storage access keys

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
- Regular security audits
- Monitor storage usage 