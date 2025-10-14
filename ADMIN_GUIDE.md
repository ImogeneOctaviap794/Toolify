# Toolify Admin Web 管理界面快速指南

## 概述

Toolify Admin 提供了一个现代化的 Web 管理界面，让您可以通过浏览器轻松管理所有配置，无需手动编辑 YAML 文件。

## 初始设置

### 1. 选择部署方式

#### 方式 A：Docker 部署（推荐）

```bash
# 1. 配置文件
cp config.example.yaml config.yaml

# 2. 初始化管理员账号（在宿主机上运行）
python init_admin.py

# 3. 构建并启动（会自动构建前端）
docker-compose up -d --build
```

Docker 部署会自动完成前端构建，无需手动操作。

#### 方式 B：直接运行

```bash
# 安装 Python 依赖（如果还没安装）
pip install -r requirements.txt

# 构建前端（首次使用或前端代码更新后）
./build_frontend.sh
```

### 2. 配置管理员账号

管理界面已经预配置了默认账号：

- **用户名**: `admin`
- **密码**: `admin123`

⚠️ **安全提示**: 建议在生产环境中修改默认密码！

要修改管理员账号，运行：

```bash
python init_admin.py
```

按照提示输入新的用户名和密码，脚本会自动更新 `config.yaml`。

## 启动服务

### Docker 方式

```bash
docker-compose up -d --build
```

### 直接运行方式

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。

## 访问管理界面

1. 打开浏览器访问: `http://localhost:8000/admin`
2. 使用管理员账号登录
3. 开始管理配置！

## 功能说明

### 1. 服务器配置

管理 Toolify 服务器的基本运行参数：

- **监听地址**: 服务器监听的 IP 地址
- **监听端口**: 服务器监听的端口号（1-65535）
- **请求超时**: 上游服务请求的超时时间（秒）

### 2. 上游服务管理

添加、编辑和删除上游 LLM 服务配置：

- **服务名称**: 用于标识的服务名称
- **Base URL**: 上游服务的 API 地址
- **API Key**: 上游服务的 API 密钥
- **优先级**: 数字越小优先级越高（0 为最高），支持多渠道故障转移
- **支持的模型**: 该服务支持的模型列表（每行一个）
- **默认服务**: 是否设为默认服务（当请求的模型不在任何服务列表中时使用）

**模型别名格式**: 支持使用 `alias:real-model` 格式，例如 `gemini:gemini-2.5-pro`

**多渠道配置**: 可以为同一个模型配置多个服务（如多个 OpenAI 代理），系统会按优先级顺序尝试，当一个渠道失败时自动切换到下一个

### 3. 客户端认证

管理允许访问 Toolify 服务的客户端 API 密钥：

- 添加新的 API Key
- 删除现有的 API Key
- 客户端需要在请求头中携带：`Authorization: Bearer YOUR_API_KEY`

### 4. 功能配置

切换各项功能开关和行为参数：

- **启用函数调用**: 为不支持的 LLM 注入函数调用能力
- **转换 Developer 角色**: 将 developer 角色转换为 system 角色
- **Key 透传模式**: 直接转发客户端提供的 API Key
- **Model 透传模式**: 将所有请求转发到 'openai' 服务
- **日志级别**: 控制日志输出详细程度（DEBUG/INFO/WARNING/ERROR/CRITICAL/DISABLED）

## 保存配置

点击右上角的 **"保存配置"** 按钮保存所有修改。

⚠️ **重要**: 配置保存后，您需要**手动重启** Toolify 服务才能使更改生效！

```bash
# 停止服务（Ctrl+C 或 kill 进程）
# 然后重新启动
python main.py
```

## 前端开发

如果您需要修改管理界面的前端代码：

```bash
# 进入前端目录
cd frontend

# 安装依赖（首次）
npm install

# 开发模式（支持热重载）
npm run dev
# 访问 http://localhost:3000

# 构建生产版本
npm run build
```

前端技术栈：
- **React 19** + TypeScript
- **Vite** 构建工具
- **Tailwind CSS** + **shadcn/ui** 组件库

## 安全建议

1. **修改默认密码**: 首次部署后立即修改默认管理员密码
2. **使用 HTTPS**: 在生产环境中配置 HTTPS
3. **限制访问**: 考虑使用防火墙限制管理界面的访问
4. **定期更新**: 保持 Toolify 及其依赖项更新到最新版本

## 故障排查

### 无法访问管理界面

**Docker 部署**：
1. 检查容器是否运行：`docker ps | grep toolify`
2. 查看容器日志：`docker logs toolify`
3. 进入容器检查：`docker exec -it toolify ls -la frontend/dist`

**直接运行**：
1. 检查服务是否正常运行：`curl http://localhost:8000/`
2. 确认前端已构建：检查 `frontend/dist` 目录是否存在
3. 查看日志文件：`tail -f toolify.log`

### 登录失败

1. 确认用户名和密码正确
2. 检查 `config.yaml` 中的 `admin_authentication` 配置
3. 验证密码哈希是否正确生成

### 配置保存失败

1. 检查配置格式是否正确
2. 查看错误提示信息
3. 确认 `config.yaml` 文件有写入权限

## 技术支持

如有问题，请访问：
- GitHub Issues: https://github.com/funnycups/toolify/issues
- 项目文档: README.md

---

**享受使用 Toolify Web 管理界面！** 🎉

