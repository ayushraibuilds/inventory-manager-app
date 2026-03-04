FROM node:20-alpine

WORKDIR /app

# Deps
COPY package.json package-lock.json* ./
RUN npm ci

# App code
COPY . .

# Build arg for API URL (baked into the Next.js bundle at build time)
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
