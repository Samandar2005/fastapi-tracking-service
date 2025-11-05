FROM node:20-alpine
WORKDIR /app

# Copy package.json va package-lock.json
COPY package.json package-lock.json* ./

# NPM install + legacy peer deps
RUN npm install --legacy-peer-deps

# PATH ga node_modules/.bin qo‘shish
ENV PATH=/app/node_modules/.bin:$PATH

# Copy frontend code
COPY . .

# CMD
CMD ["npm", "run", "dev", "--", "--host"]
