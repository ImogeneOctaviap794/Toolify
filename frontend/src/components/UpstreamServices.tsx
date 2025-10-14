import { ConfigData } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Button } from './ui/button'
import { Switch } from './ui/switch'
import { Plus, Trash2, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

interface UpstreamServicesProps {
  config: ConfigData
  setConfig: (config: ConfigData) => void
}

export default function UpstreamServices({ config, setConfig }: UpstreamServicesProps) {
  const [expandedServices, setExpandedServices] = useState<Set<number>>(new Set([0]))

  const addService = () => {
    const newService = {
      name: `service-${config.upstream_services.length + 1}`,
      base_url: 'https://api.example.com/v1',
      api_key: '',
      description: '',
      is_default: false,
      priority: config.upstream_services.length,
      models: []
    }
    setConfig({
      ...config,
      upstream_services: [...config.upstream_services, newService]
    })
  }

  const removeService = (index: number) => {
    const services = config.upstream_services.filter((_, i) => i !== index)
    setConfig({
      ...config,
      upstream_services: services
    })
  }

  const updateService = (index: number, field: string, value: any) => {
    const services = [...config.upstream_services]
    if (field === 'is_default' && value) {
      // Ensure only one default service
      services.forEach((s, i) => {
        s.is_default = i === index
      })
    } else {
      ;(services[index] as any)[field] = value
    }
    setConfig({
      ...config,
      upstream_services: services
    })
  }

  const updateModels = (index: number, modelsText: string) => {
    const models = modelsText
      .split('\n')
      .map((m) => m.trim())
      .filter((m) => m.length > 0)
    updateService(index, 'models', models)
  }

  const toggleExpand = (index: number) => {
    const newExpanded = new Set(expandedServices)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedServices(newExpanded)
  }

  return (
    <div className="space-y-4">
      {config.upstream_services.map((service, index) => (
        <Card key={index}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <CardTitle className="flex items-center gap-2">
                  {service.name}
                  {service.is_default && (
                    <span className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded">
                      默认
                    </span>
                  )}
                  {(!service.api_key || service.api_key.trim() === '') && (
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded border border-yellow-300">
                      未配置密钥
                    </span>
                  )}
                  {service.models.length === 0 && (
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded border border-gray-300">
                      未配置模型
                    </span>
                  )}
                </CardTitle>
                <CardDescription>{service.description || '上游服务配置'}</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleExpand(index)}
                >
                  {expandedServices.has(index) ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </Button>
                {config.upstream_services.length > 1 && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => removeService(index)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>

          {expandedServices.has(index) && (
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>服务名称</Label>
                  <Input
                    value={service.name}
                    onChange={(e) => updateService(index, 'name', e.target.value)}
                    placeholder="服务名称"
                  />
                </div>

                <div className="space-y-2">
                  <Label>描述</Label>
                  <Input
                    value={service.description || ''}
                    onChange={(e) => updateService(index, 'description', e.target.value)}
                    placeholder="服务描述（可选）"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor={`priority-${index}`}>优先级</Label>
                  <Input
                    id={`priority-${index}`}
                    type="number"
                    value={service.priority}
                    onChange={(e) => updateService(index, 'priority', parseInt(e.target.value) || 0)}
                    placeholder="0"
                    min="0"
                  />
                  <p className="text-sm text-muted-foreground">
                    数字越小优先级越高，0为最高
                  </p>
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label>Base URL</Label>
                  <Input
                    value={service.base_url}
                    onChange={(e) => updateService(index, 'base_url', e.target.value)}
                    placeholder="https://api.example.com/v1"
                  />
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label>API Key</Label>
                  <Input
                    type="password"
                    value={service.api_key}
                    onChange={(e) => updateService(index, 'api_key', e.target.value)}
                    placeholder="API 密钥"
                  />
                  <p className="text-sm text-muted-foreground">
                    💡 提示：可以保存空密钥作为占位符配置，实际使用时会自动跳过
                  </p>
                </div>

                <div className="space-y-2 md:col-span-2">
                  <Label>支持的模型（每行一个）</Label>
                  <textarea
                    className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    value={service.models.join('\n')}
                    onChange={(e) => updateModels(index, e.target.value)}
                    placeholder="gpt-3.5-turbo&#10;gpt-4&#10;claude-2"
                  />
                  <p className="text-sm text-muted-foreground">
                    支持别名格式：alias:real-model（如 gemini:gemini-2.5-pro）
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <Switch
                    checked={service.is_default}
                    onCheckedChange={(checked) => updateService(index, 'is_default', checked)}
                  />
                  <Label>设为默认服务</Label>
                </div>
              </div>
            </CardContent>
          )}
        </Card>
      ))}

      <Button onClick={addService} variant="outline" className="w-full">
        <Plus className="w-4 h-4 mr-2" />
        添加上游服务
      </Button>

      <Card>
        <CardHeader>
          <CardTitle>多渠道优先级说明</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Toolify Admin 支持为同一个模型配置多个上游渠道，并按优先级进行故障转移。
            </p>
            
            <div className="bg-muted/50 border rounded-lg p-4">
              <h4 className="font-medium mb-2">工作原理</h4>
              <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
                <li><strong>优先级</strong>：数字越小优先级越高（0 为最高优先级）</li>
                <li><strong>自动故障转移</strong>：当高优先级渠道返回 429（限流）或 5xx 错误时，自动切换到下一优先级渠道</li>
                <li><strong>同模型多渠道</strong>：可以为同一个模型配置多个服务（如 gpt-4 配置多个 OpenAI 代理）</li>
                <li><strong>流式请求</strong>：始终使用最高优先级渠道（因为流式响应无法中途切换）</li>
                <li><strong>客户端错误</strong>：400/401/403 等客户端错误不会触发故障转移</li>
                <li><strong>占位符配置</strong>：可以保存空 API Key 或空模型列表的服务，系统会自动跳过，方便提前规划配置</li>
              </ul>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium mb-2 text-blue-900">配置示例</h4>
              <pre className="text-xs text-blue-800 overflow-x-auto">
{`upstream_services:
  - name: "openai-primary"
    priority: 0  # 主渠道
    models: ["gpt-4", "gpt-4o"]
  
  - name: "openai-backup"
    priority: 1  # 备用渠道
    models: ["gpt-4", "gpt-4o"]`}
              </pre>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

