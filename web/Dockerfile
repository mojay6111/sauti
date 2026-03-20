FROM node:20-alpine AS base

WORKDIR /app
COPY package.json ./
RUN npm install

COPY . .

FROM base AS dev
CMD ["npm", "run", "dev"]

FROM base AS builder
RUN npm run build

FROM node:20-alpine AS production
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
EXPOSE 3000
CMD ["npm", "start"]
