import { ConfigData } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Label } from './ui/label'
import { Switch } from './ui/switch'

interface FeaturesProps {
  config: ConfigData
  setConfig: (config: ConfigData) => void
}

export default function Features({ config, setConfig }: FeaturesProps) {
  const updateFeature = (field: keyof ConfigData['features'], value: any) => {
    setConfig({
      ...config,
      features: {
        ...config.features,
        [field]: value
      }
    })
  }

  const logLevels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'DISABLED']

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>功能配置</CardTitle>
          <CardDescription>
            配置 Toolify 的功能开关和行为参数
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>启用函数调用</Label>
              <p className="text-sm text-muted-foreground">
                为不支持原生函数调用的 LLM 注入函数调用能力
              </p>
            </div>
            <Switch
              checked={config.features.enable_function_calling}
              onCheckedChange={(checked) => updateFeature('enable_function_calling', checked)}
            />
          </div>

          <div className="border-t pt-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>转换 Developer 角色</Label>
                <p className="text-sm text-muted-foreground">
                  将 developer 角色转换为 system 角色以提高兼容性
                </p>
              </div>
              <Switch
                checked={config.features.convert_developer_to_system}
                onCheckedChange={(checked) => updateFeature('convert_developer_to_system', checked)}
              />
            </div>
          </div>

          <div className="border-t pt-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Key 透传模式</Label>
                <p className="text-sm text-muted-foreground">
                  直接转发客户端提供的 API Key 到上游，而不使用配置的密钥
                </p>
              </div>
              <Switch
                checked={config.features.key_passthrough}
                onCheckedChange={(checked) => updateFeature('key_passthrough', checked)}
              />
            </div>
          </div>

          <div className="border-t pt-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Model 透传模式</Label>
                <p className="text-sm text-muted-foreground">
                  将所有请求直接转发到 'openai' 上游服务，忽略模型路由
                </p>
              </div>
              <Switch
                checked={config.features.model_passthrough}
                onCheckedChange={(checked) => updateFeature('model_passthrough', checked)}
              />
            </div>
          </div>

          <div className="border-t pt-6">
            <div className="space-y-2">
              <Label htmlFor="log-level">日志级别</Label>
              <select
                id="log-level"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={config.features.log_level}
                onChange={(e) => updateFeature('log_level', e.target.value)}
              >
                {logLevels.map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
              <p className="text-sm text-muted-foreground">
                控制日志输出的详细程度
              </p>
            </div>
          </div>

          {config.features.prompt_template && (
            <div className="border-t pt-6">
              <div className="space-y-2">
                <Label htmlFor="prompt-template">自定义提示词模板</Label>
                <textarea
                  id="prompt-template"
                  className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  value={config.features.prompt_template || ''}
                  onChange={(e) => updateFeature('prompt_template', e.target.value)}
                  placeholder="自定义提示词模板（可选）"
                />
                <p className="text-sm text-muted-foreground">
                  必须包含 {'{tools_list}'} 和 {'{trigger_signal}'} 占位符
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>功能说明</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium mb-2">日志级别说明</h4>
            <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
              <li><strong>DEBUG</strong>: 显示所有调试信息（最详细）</li>
              <li><strong>INFO</strong>: 显示一般信息、警告和错误</li>
              <li><strong>WARNING</strong>: 仅显示警告和错误</li>
              <li><strong>ERROR</strong>: 仅显示错误</li>
              <li><strong>CRITICAL</strong>: 仅显示严重错误</li>
              <li><strong>DISABLED</strong>: 禁用所有日志记录</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

