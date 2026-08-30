FROM node:20-alpine

WORKDIR /app

# Install dependencies first for better caching
COPY package*.json ./
RUN npm install

# Copy the rest of the application
COPY . .

# Expose port 3000 (as configured in vite.config.ts)
EXPOSE 3000

# Start the Vite development server
CMD ["npm", "run", "dev"]
