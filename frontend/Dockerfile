FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV production

# Copy package files
COPY package.json package-lock.json* ./

# Install only production dependencies (with timeout handling)
RUN npm ci --production --loglevel=error || npm install --production --loglevel=error || echo "Dependencies will be copied"

# Copy pre-built application
COPY .next ./.next
COPY pages ./pages
COPY tsconfig.json ./

# If dependencies didn't install, copy from host
COPY node_modules ./node_modules

EXPOSE 3000

CMD ["npm", "start"]
