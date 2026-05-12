FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# Optional absolute API origin for the browser. Empty = same origin / Vite proxy (see vite.config).
ARG VITE_API_URL=
ENV VITE_API_URL=${VITE_API_URL}

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
