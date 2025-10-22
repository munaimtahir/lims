FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY pages ./pages
COPY tsconfig.json ./

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0"]
