# Stage 1: Build & Prune
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Set build-time env vars so relative routing is baked into the browser build
ARG NEXT_PUBLIC_API_BASE_URL=""
ARG NEXT_PUBLIC_TESTCASE_API_BASE_URL=""
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
ENV NEXT_PUBLIC_TESTCASE_API_BASE_URL=${NEXT_PUBLIC_TESTCASE_API_BASE_URL}
RUN npm run build
RUN npm prune --production

# Stage 2: Runner
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app /app
EXPOSE 3000
CMD ["npx", "next", "start", "-p", "3000"]
