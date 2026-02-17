# ===== Frontend Dockerfile =====
# 跨平台支持 ARM64 + AMD64

# Stage 1: 编译
FROM node:20-slim AS builder

WORKDIR /app

COPY package.json ./
RUN npm install --registry=https://registry.npmmirror.com

COPY . .
RUN npm run build

# Stage 2: 运行
FROM nginx:stable-alpine

# 复制编译产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
