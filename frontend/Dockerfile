FROM node:20

WORKDIR /app

# Copy JSON files except the lock
COPY package*.json ./
RUN rm -f package-lock.json
RUN npm install

# Copy the rest of the frontend code
COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
