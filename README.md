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

2. Create a `.env` file:
   - Copy `.env.example` to `.env`
   - Fill in your environment variables
   - NEVER commit the `.env` file to version control

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