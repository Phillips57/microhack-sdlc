FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist/ /usr/share/nginx/html/
COPY --from=builder /app/public/* /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY entrypoint.sh /entrypoint.sh

# Set proper permissions for the nginx html directory and entrypoint script
RUN chmod -R 755 /usr/share/nginx/html && \
    chown -R nginx:nginx /usr/share/nginx/html && \
    chmod +x /entrypoint.sh

# Set default environment variables
ENV API_HOST=api \
    API_PORT=80 \
    NGINX_ENVSUBST_FILTER='^API_HOST$|^API_PORT$'

EXPOSE 80

# Generate runtime config before using the official nginx entrypoint.
ENTRYPOINT ["/entrypoint.sh"]
