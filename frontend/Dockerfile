FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
ENV NITRO_PRESET=node-server
RUN npm run build

EXPOSE 8080

# Cloud Run injects the PORT environment variable. Nitro automatically listens to process.env.PORT.
ENV PORT=8080
ENV HOST=0.0.0.0
ENV NODE_ENV=production

CMD ["node", ".output/server/index.mjs"]
