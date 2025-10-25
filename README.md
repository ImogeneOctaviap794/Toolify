<div align="center">

# 🚀 Toolify Admin

[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6.svg)](https://www.typescriptlang.org/)

**Empower any LLM with Function Calling + Visual Admin Interface**

[English](README.md) | [简体中文](README_zh.md)

[Quick Start](#-quick-start) • [Features](#-key-features) • [Documentation](#-usage) • [Admin UI](#-web-admin-interface) • [Contributing](#-contributing)

---

### 📊 Project Origin & Acknowledgments

> Based on [funnycups/toolify](https://github.com/funnycups/toolify)  
> Special thanks to **FunnyCups** for creating the excellent Toolify middleware

### ✨ Key Enhancements

- 🎨 **Web Admin UI** - React 19 + TypeScript visual configuration
- ⚡ **Real-time Reload** - Config changes take effect instantly
- 🔄 **Multi-Channel Failover** - Smart priority-based routing
- 🌐 **Multi-API Support** - OpenAI + Anthropic Claude formats
- 📱 **Responsive Design** - Perfect for mobile and desktop

</div>

---

## 📖 Introduction

**Toolify Admin** is a powerful LLM function calling middleware proxy designed for enterprise applications. It injects OpenAI-compatible function calling capabilities into Large Language Models through **Prompt Injection** technology, while providing a modern web-based admin interface for visual configuration management.

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🎯 Function Calling

- 🔌 **Universal Support** - Inject function calling into any LLM
- 📦 **Multi-Function** - Execute multiple functions concurrently
- ⚡ **Flexible Trigger** - Initiate calls at any stage
- 🧠 **Think Tag Safe** - Seamlessly handle thinking process
- 🌊 **Streaming** - Full streaming support with real-time parsing
- 🎨 **Context Enhanced** - Improved model understanding

</td>
<td width="50%">

### 🛡️ Enterprise Features

- 🔄 **Multi-Channel Failover** - Smart priority-based routing
- 🌐 **Multi-API Format** - OpenAI + Anthropic Claude support
- 🔐 **Secure Auth** - JWT Token + bcrypt encryption
- ⚡ **Real-time Reload** - Zero-downtime config updates
- 📊 **Visual Management** - Modern web interface
- 📱 **Responsive** - Works on desktop, tablet, mobile

</td>
</tr>
</table>

## How It Works

1. **Intercept Request**: Toolify intercepts the `chat/completions` request from the client, which includes the desired tools.
2. **Inject Prompt**: It generates a specific system prompt instructing the LLM how to output function calls using a structured XML format and a unique trigger signal.
3. **Proxy to Upstream**: The modified request is sent to the configured upstream LLM service.
4. **Parse Response**: Toolify analyzes the upstream response. If the trigger signal is detected, it parses the XML structure to extract the function calls.
5. **Format Response**: It transforms the parsed tool calls into the standard OpenAI `tool_calls` format and sends it back to the client.

## Installation and Setup

You can run Toolify using Docker Compose or Python directly.

### Option 1: Using Docker Compose

This is the recommended way for easy deployment.

#### Prerequisites

- Docker and Docker Compose installed.

#### Steps

1. **Clone the repository:**

   ```bash
   git clone https://github.com/ImogeneOctaviap794/Toolify.git
   cd Toolify
   ```

2. **Configure the application:**

   Copy the example configuration file and edit it:

   ```bash
   cp config.example.yaml config.yaml
   ```

   Edit `config.yaml`. Make sure to add `admin_authentication` configuration (for the web admin interface):

   ```yaml
   admin_authentication:
     username: "admin"
     password: "$2b$12$..."  # Use init_admin.py to generate
     jwt_secret: "your-secure-random-jwt-secret-min-32-chars"
   ```

   Or use the `init_admin.py` script to generate automatically:

   ```bash
   python init_admin.py
   ```

3. **Start the service:**

   ```bash
   docker-compose up -d --build
   ```

   This will build the Docker image (including the frontend admin interface) and start the Toolify service in detached mode.

   - API Service: `http://localhost:8000`
   - Admin Interface: `http://localhost:8000/admin`

   **Note**: The frontend will be compiled during Docker build, which may take a few minutes on first build.

### Option 2: Using Python

#### Prerequisites

- Python 3.8+

#### Steps

1. **Clone the repository:**

   ```bash
   git clone https://github.com/funnycups/toolify.git
   cd toolify
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application:**

   Copy the example configuration file and edit it:

   ```bash
   cp config.example.yaml config.yaml
   ```

   Edit `config.yaml` to set up your upstream services, API keys, and allowed client keys.

4. **Run the server:**

   ```bash
   python main.py
   ```

## Configuration (`config.yaml`)

Refer to [`config.example.yaml`](config.example.yaml) for detailed configuration options.

- **`server`**: Middleware host, port, and timeout settings.
- **`upstream_services`**: List of upstream LLM providers (e.g., Groq, OpenAI, Anthropic).
  - Define `base_url`, `api_key`, supported `models`, and set one service as `is_default: true`.
- **`client_authentication`**: List of `allowed_keys` for clients accessing this middleware.
- **`features`**: Toggle features like logging, role conversion, and API key handling.
  - `key_passthrough`: Set to `true` to directly forward the client-provided API key to the upstream service, bypassing the configured `api_key` in `upstream_services`.
  - `model_passthrough`: Set to `true` to forward all requests directly to the upstream service named 'openai', ignoring any model-based routing rules.
  - `prompt_template`: Customize the system prompt used to instruct the model on how to use tools.

## Usage

Once Toolify is running, configure your client application (e.g., using the OpenAI SDK) to use Toolify's address as the `base_url`. Use one of the configured `allowed_keys` for authentication.

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",  # Toolify endpoint
    api_key="sk-my-secret-key-1"          # Your configured client key
)

# The rest of your OpenAI API calls remain the same, including tool definitions.
```

Toolify handles the translation between the standard OpenAI tool format and the prompt-based method required by unsupported LLMs.

## Multi-Channel Priority & Failover

Toolify Admin supports configuring multiple upstream channels for the same model with priority-based automatic failover, significantly improving service availability and stability.

### Features

- **Priority Mechanism**: Configure `priority` value for each service (higher number = higher priority, 100 > 50)
- **No Default Service Required**: Removed `is_default` requirement, automatically uses highest priority service as fallback
- **Automatic Failover**: Automatically try next priority channel when high-priority channel fails
- **Smart Retry Strategy**:
  - For 429 (rate limit) and 5xx (server errors): Automatically switch to backup channel
  - For 400/401/403 (client errors): No retry (would fail on other channels too)
- **Same Model Multi-Channel**: Configure multiple OpenAI proxies or mirrors for the same model
- **Transparent Switching**: Completely transparent to clients, handles all failover logic automatically

### Configuration Example

```yaml
upstream_services:
  # Primary channel - highest priority
  - name: "openai-primary"
    base_url: "https://api.openai.com/v1"
    api_key: "your-primary-key"
    priority: 100  # Highest priority (higher number = higher priority)
    models:
      - "gpt-4"
      - "gpt-4o"
      - "gpt-3.5-turbo"
  
  # Backup channel - second priority
  - name: "openai-backup"
    base_url: "https://api.openai-proxy.com/v1"
    api_key: "your-backup-key"
    priority: 50  # Second priority
    models:
      - "gpt-4"
      - "gpt-4o"
  
  # Third priority channel
  - name: "openai-fallback"
    base_url: "https://another-proxy.com/v1"
    api_key: "your-fallback-key"
    priority: 10
    models:
      - "gpt-4"
```

### Workflow

1. Request `gpt-4` model
2. System first tries `priority: 100` channel (openai-primary) - highest priority
3. If returns 429 or 500+ error, automatically switches to `priority: 50` channel (openai-backup)
4. If still fails, continues to try `priority: 10` channel (openai-fallback)
5. Only returns error to client when all channels have failed

### Notes

- **Priority Rule**: Higher number = higher priority (recommend using intervals like 100/50/10 for easy insertion of intermediate priorities)
- **Streaming Requests**: Due to the nature of streaming responses, always uses highest priority channel (cannot switch mid-stream)
- **Same Priority**: Multiple services can have same priority, in which case they're tried in config file order
- **Model Matching**: Only services configured with the same model participate in failover
- **is_default Deprecated**: No longer need to set default service, system automatically uses highest priority service as fallback

## Web Admin Interface

Toolify provides a modern web-based admin interface for easy configuration management through your browser.

### Initialize Admin Account

Before using the admin interface, initialize an admin account:

```bash
python init_admin.py
```

Follow the prompts to enter a username and password. The script will automatically generate a hashed password and JWT secret, then update your `config.yaml` file.

Alternatively, you can manually add the following configuration to `config.yaml`:

```yaml
admin_authentication:
  username: "admin"
  password: "$2b$12$..."  # bcrypt hashed password
  jwt_secret: "your-secure-random-jwt-secret-min-32-chars"
```

### Access Admin Interface

1. Start the Toolify service
2. Open `http://localhost:8000/admin` in your browser
3. Login with your admin credentials

### Features

- 📊 **Server Configuration**: Manage host, port, and timeout settings
- 🔄 **Upstream Services**: Add, edit, and remove upstream LLM service configurations
- 🔑 **Client Authentication**: Manage client API keys
- ⚙️ **Feature Configuration**: Toggle feature flags and behavior parameters
- 💾 **Real-time Saving**: Changes are saved directly to `config.yaml`
- 🔐 **Secure Authentication**: JWT-based secure login system

### Frontend Development

If you need to modify the admin interface frontend:

```bash
# Install dependencies
cd frontend
npm install

# Development mode (with hot reload)
npm run dev

# Build for production
npm run build

# Or use the build script
cd ..
./build_frontend.sh
```

Frontend Tech Stack:
- React 19 + TypeScript
- Vite build tool
- Tailwind CSS + shadcn/ui component library

## License

This project is licensed under the GPL-3.0-or-later license.