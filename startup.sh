#!/bin/bash

# Add Microsoft repository
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Install ODBC Driver
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17
ACCEPT_EULA=Y apt-get install -y mssql-tools
apt-get install -y unixodbc-dev

# Add SQL Server tools to path
echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc

# Start the Python application
cd /home/site/wwwroot
gunicorn --bind=0.0.0.0:8000 --timeout=600 app:app 