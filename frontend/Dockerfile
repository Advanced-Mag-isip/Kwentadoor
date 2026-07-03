FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

ARG PUBLIC_API_URL
ARG INTERNAL_API_URL
ENV PUBLIC_API_URL=$PUBLIC_API_URL
ENV INTERNAL_API_URL=$INTERNAL_API_URL

RUN npm run build

FROM node:22-alpine AS runner

WORKDIR /app

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 4321

CMD ["node", "./dist/server/entry.mjs"]