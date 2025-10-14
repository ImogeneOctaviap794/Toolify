# Toolify Admin

[English](README.md) | [简体中文](README_zh.md)

> **Project Origin**: This project is based on [funnycups/toolify](https://github.com/funnycups/toolify)  
> **Key Enhancements**: Added web admin interface with visual configuration management and real-time config reload  
> **Acknowledgments**: Special thanks to FunnyCups for creating the excellent Toolify middleware project

---

**Empower any LLM with function calling capabilities, plus a visual admin interface.**

Toolify Admin is an enhanced version of the Toolify middleware proxy with added management features. It injects OpenAI-compatible function calling capabilities into Large Language Models that lack native support, while providing a modern web-based admin interface for easy configuration management without manually editing YAML files.

## Key Features

- **Universal Function Calling**: Enables function calling for LLMs or APIs that adhere to the OpenAI format but lack native support.
- **Multiple Function Calls**: Supports executing multiple functions simultaneously in a single response.
- **Flexible Initiation**: Allows function calls to be initiated at any stage of the model's output.
- **Think Tag Compatibility**: Seamlessly handles `<think>` tags, ensuring they don't interfere with tool parsing.
- **Streaming Support**: Fully supports streaming responses, detecting and parsing function calls on the fly.
- **Multi-Service Routing**: Routes requests to different upstream services based on the requested model name.
- **Client Authentication**: Secures the middleware with configurable client API keys.
- **Enhanced Context Awareness**: Provides LLMs with the details (name and parameters) of previous tool calls alongside the execution results, improving contextual understanding.
- **Web Admin Interface**: Modern web-based UI for managing all configuration options visually, no need to manually edit YAML files.

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