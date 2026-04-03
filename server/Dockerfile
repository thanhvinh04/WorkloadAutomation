# Use official Python runtime as base image
FROM python:3.12

# Set working directory
WORKDIR /app

# Copy requirements file
COPY server/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server/ .

# Explicitly copy sensitive config files to ensure they're included
COPY server/ServerPassword.json /app/ServerPassword.json
COPY server/Account_LS_EHD_MANAGEMENT.json /app/Account_LS_EHD_MANAGEMENT.json

# Verify critical files exist
RUN ls -la /app/ServerPassword.json /app/Account_LS_EHD_MANAGEMENT.json || echo "Warning: Config files not found"

# Set environment variables
ENV PHOTO8_PYTHON_EXE=/usr/local/bin/python
ENV PHOTO8_JWT_SECRET=@Le@dingSt@r@123
ENV PHOTO8_JWT_ISSUER=photo8-api
ENV PHOTO8_JWT_AUDIENCE=photo8-client
ENV PHOTO8_JWT_EXPIRE_MINUTES=120
ENV PYTHONPATH=/app
ENV HADDAD_SQL_CONFIG=/app/ServerPassword.json
ENV HADDAD_GS_SERVICE_JSON=/app/Account_LS_EHD_MANAGEMENT.json

RUN export DEBIAN_FRONTEND=noninteractive \
    # Calculate the Debian version dynamically, just like your script
    && VERSION_ID=$(grep VERSION_ID /etc/os-release | cut -d '"' -f 2 | cut -d '.' -f 1) \
    \
    # Download the package configuration
    && curl -sSL -O https://packages.microsoft.com/config/debian/$VERSION_ID/packages-microsoft-prod.deb \
    \
    # Install the package
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    \
    # Update apt lists to see the new Microsoft repo
    && apt-get update \
    \
    # Install the drivers and tools (accepting EULA)
    && ACCEPT_EULA=Y apt-get install -y \
        msodbcsql18 \
        mssql-tools18 \
        unixodbc-dev \
        libgssapi-krb5-2 \
    \
    # Clean up apt cache to save space
    && rm -rf /var/lib/apt/lists/*

ENV PATH="$PATH:/opt/mssql-tools18/bin"

# Expose port
EXPOSE 8000

# Health check
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:8000/docs || exit 1

# Command to run the app
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
