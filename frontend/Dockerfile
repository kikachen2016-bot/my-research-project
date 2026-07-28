FROM node:20-alpine
WORKDIR /frontend
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN chmod +x node_modules/.bin/next
EXPOSE 3000
CMD ["npm", "run", "dev"]
