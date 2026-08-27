# Stage 1: Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy package lock and manifest for layer caching
COPY package*.json ./

RUN npm ci

# Copy application source files
COPY . .

# Accept VITE_API_URL as a build argument
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

# Build static production assets
RUN npm run build

# Stage 2: Production stage using Nginx
FROM nginx:1.25-alpine AS production

# Copy custom Nginx configuration for single-page application (SPA) routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build output from build stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
