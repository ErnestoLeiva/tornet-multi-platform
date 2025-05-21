FROM python:3.11-slim

# Set Docker environment variable
ENV DOCKER_ENV=true

# Install dependencies with retry mechanism to handle repository issues
RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /var/lib/apt/lists/partial && \
    apt-get clean && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        tor \
        python3-pip \
        sudo \
        procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Fix permissions for Tor directories
RUN chmod 700 /var/lib/tor && \
    mkdir -p /var/run/tor && \
    chmod 700 /var/run/tor && \
    chown -R debian-tor:debian-tor /var/lib/tor && \
    chown -R debian-tor:debian-tor /var/run/tor && \
    chmod 700 /var/log/tor

# Set working directory
WORKDIR /app

# Copy the package files
COPY . .

# Install the package
RUN pip3 install --no-cache-dir .

# Create a configuration file for Tor that sets the SOCKS port to 9050
RUN echo "SocksPort 0.0.0.0:9050" > /etc/tor/torrc \
    && echo "SocksPolicy accept *" >> /etc/tor/torrc \
    && echo "Log notice stdout" >> /etc/tor/torrc \
    && echo "DataDirectory /var/lib/tor" >> /etc/tor/torrc \
    && echo "RunAsDaemon 0" >> /etc/tor/torrc

# Expose the Tor SOCKS proxy port
EXPOSE 9050

# Create a startup script that properly starts Tor
RUN echo '#!/bin/bash\necho "Starting Tor..."\nchown -R debian-tor:debian-tor /var/lib/tor\n\n# Start Tor as the debian-tor user\nsudo -u debian-tor tor -f /etc/tor/torrc &\n\n# Wait for Tor to establish connections\nsleep 5\n\n# Run tornet in the foreground\necho "Starting TorNet IP rotation service..."\ntornet --interval 60 --count 0' > /app/start.sh \
    && chmod +x /app/start.sh

# Run the startup script when the container starts
CMD ["/app/start.sh"]