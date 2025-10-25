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
    <div className="space-y-6">
      <Card className="shadow-md border-gray-200">
        <CardHeader className="bg-gradient-to-r from-white to-gray-50 border-b border-gray-100">
          <CardTitle className="text-xl text-gray-800 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600"></div>
            功能配置
          </CardTitle>
          <CardDescription className="text-gray-600">
            配置 Toolify 的功能开关和行为参数
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 p-6">
          <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200">
            <div className="space-y-1">
              <Label className="font-medium text-gray-800 flex items-center gap-2">
                <span className="text-purple-500">🔄</span>
                转换 Developer 角色
              </Label>
              <p className="text-sm text-gray-600">
                将 developer 角色转换为 system 角色以提高兼容性
              </p>
            </div>
            <Switch
              checked={config.features.convert_developer_to_system}
              onCheckedChange={(checked) => updateFeature('convert_developer_to_system', checked)}
              className="data-[state=checked]:bg-purple-500"
            />
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200">
            <div className="space-y-1">
              <Label className="font-medium text-gray-800 flex items-center gap-2">
                <span className="text-green-500">🔑</span>
                Key 透传模式
              </Label>
              <p className="text-sm text-gray-600">
                直接转发客户端提供的 API Key 到上游，而不使用配置的密钥
              </p>
            </div>
            <Switch
              checked={config.features.key_passthrough}
              onCheckedChange={(checked) => updateFeature('key_passthrough', checked)}
              className="data-[state=checked]:bg-green-500"
            />
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200">
            <div className="space-y-1">
              <Label className="font-medium text-gray-800 flex items-center gap-2">
                <span className="text-orange-500">🚀</span>
                Model 透传模式
              </Label>
              <p className="text-sm text-gray-600">
                使用所有配置的上游服务，按优先级路由，忽略模型匹配
              </p>
            </div>
            <Switch
              checked={config.features.model_passthrough}
              onCheckedChange={(checked) => updateFeature('model_passthrough', checked)}
              className="data-[state=checked]:bg-orange-500"
            />
          </div>

          <div className="space-y-2 p-4 rounded-lg bg-gray-50 border border-gray-200">
            <Label htmlFor="log-level" className="font-medium text-gray-700 flex items-center gap-2">
              <span className="text-gray-600">📄</span>
              日志级别
            </Label>
            <select
              id="log-level"
              className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors"
              value={config.features.log_level}
              onChange={(e) => updateFeature('log_level', e.target.value)}
            >
              {logLevels.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
            <p className="text-sm text-gray-500">
              控制日志输出的详细程度
            </p>
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

      <Card className="shadow-md border-gray-200">
        <CardHeader className="bg-gradient-to-r from-indigo-50 to-purple-50 border-b border-indigo-100">
          <CardTitle className="text-lg text-gray-800 flex items-center gap-2">
            <span className="text-indigo-500">💡</span>
            功能说明
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6 bg-gradient-to-br from-white to-indigo-50/30">
          <div className="bg-white rounded-lg p-4 border border-indigo-100">
            <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <span className="text-blue-500">📊</span>
              日志级别说明
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <div className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">•</span>
                <div>
                  <span className="font-medium text-gray-700">DEBUG</span>
                  <p className="text-sm text-gray-500">显示所有调试信息</p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                <div>
                  <span className="font-medium text-gray-700">INFO</span>
                  <p className="text-sm text-gray-500">一般信息和警告</p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-yellow-500 mt-0.5">•</span>
                <div>
                  <span className="font-medium text-gray-700">WARNING</span>
                  <p className="text-sm text-gray-500">仅警告和错误</p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-orange-500 mt-0.5">•</span>
                <div>
                  <span className="font-medium text-gray-700">ERROR</span>
                  <p className="text-sm text-gray-500">仅显示错误</p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-red-500 mt-0.5">•</span>
                <div>
                  <span className="font-medium text-gray-700">CRITICAL</span>
                  <p className="text-sm text-gray-500">严重错误</p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-gray-500 mt-0.5">•</span>
                <div>
                  <span className="font-medium text-gray-700">DISABLED</span>
                  <p className="text-sm text-gray-500">禁用日志</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

