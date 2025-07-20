FROM node:18-alpine

WORKDIR /app/ai

COPY ./ai/package*.json ./
RUN npm install

COPY ./ai/ .
RUN npm run build

RUN mkdir -p /app/dist && cp -r dist /app/dist
