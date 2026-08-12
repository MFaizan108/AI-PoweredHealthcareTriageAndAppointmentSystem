FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# The `nginx` service in docker-compose.yml builds from this Dockerfile so the API-proxying,
# TLS-terminating nginx and the one serving the frontend's static build are the same container —
# one cert setup, one place to look. nginx/templates/ is still bind-mounted at runtime (envsubst
# needs real env vars, not build-time ones), so only the built assets are baked into the image here.
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
