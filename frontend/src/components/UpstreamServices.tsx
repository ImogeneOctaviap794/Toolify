import { ConfigData } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Button } from './ui/button'
import { Switch } from './ui/switch'
import { Plus, Trash2, ChevronDown, ChevronUp, Code, Edit } from 'lucide-react'
import { useState } from 'react'

interface UpstreamServicesProps {
  config: ConfigData
  setConfig: (config: ConfigData) => void
}

export default function UpstreamServices({ config, setConfig }: UpstreamServicesProps) {
  const [expandedServices, setExpandedServices] = useState<Set<number>>(new Set([0]))
  const [isJsonMode, setIsJsonMode] = useState(false)
  const [jsonText, setJsonText] = useState('')
  const [jsonError, setJsonError] = useState('')

  const addService = () => {
    const newService = {
      name: `service-${config.upstream_services.length + 1}`,
      service_type: 'openai',
      base_url: 'https://api.example.com/v1',
      api_key: '',
      description: '',
      is_default: false,
      priority: config.upstream_services.length * 10,
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

  const switchToJsonMode = () => {
    setJsonText(JSON.stringify(config.upstream_services, null, 2))
    setJsonError('')
    setIsJsonMode(true)
  }

  const applyJsonChanges = () => {
    try {
      const parsed = JSON.parse(jsonText)
      if (!Array.isArray(parsed)) {
        setJsonError('JSON 必须是数组格式')
        return
      }
      setConfig({
        ...config,
        upstream_services: parsed
      })
      setJsonError('')
      setIsJsonMode(false)
    } catch (e: any) {
      setJsonError(`JSON 解析错误: ${e.message}`)
    }
  }

  const cancelJsonMode = () => {
    setIsJsonMode(false)
    setJsonError('')
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center bg-white rounded-lg p-4 shadow-sm border border-gray-200">
        <div>
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600"></div>
            上游服务配置
          </h3>
          <p className="text-sm text-gray-600 mt-1">管理 API 服务端点，支持多渠道优先级与故障转移</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={addService}
            className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white shadow-sm"
          >
            <Plus className="w-4 h-4 mr-2" />
            添加服务
          </Button>
          <Button
            variant="outline"
            onClick={isJsonMode ? cancelJsonMode : switchToJsonMode}
            className="shadow-sm hover:shadow-md transition-all border-gray-300"
          >
            {isJsonMode ? (
              <>
                <Edit className="w-4 h-4 mr-2" />
                表单模式
              </>
            ) : (
              <>
                <Code className="w-4 h-4 mr-2" />
                JSON 模式
              </>
            )}
          </Button>
        </div>
      </div>

      {isJsonMode ? (
        <Card className="shadow-lg border-gray-200">
          <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 border-b">
            <CardTitle className="flex items-center gap-2 text-gray-800">
              <Code className="w-5 h-5 text-blue-600" />
              JSON 编辑模式
            </CardTitle>
            <CardDescription className="text-gray-600">
              直接编辑上游服务的 JSON 配置（适合高级用户）
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 p-6">
            {jsonError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
                <div className="flex items-start">
                  <svg className="w-5 h-5 text-red-400 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                  </svg>
                  <span>{jsonError}</span>
                </div>
              </div>
            )}
            
            <textarea
              className="font-mono text-sm flex min-h-[450px] w-full rounded-lg border border-gray-300 bg-gray-50 px-4 py-3 placeholder:text-gray-400 focus:bg-white focus:border-blue-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-all"
              value={jsonText}
              onChange={(e) => setJsonText(e.target.value)}
              placeholder="在此编辑 JSON 配置..."
            />
            
            <div className="flex justify-end gap-3 pt-2">
              <Button variant="outline" onClick={cancelJsonMode} className="hover:bg-gray-50">
                取消
              </Button>
              <Button onClick={applyJsonChanges} className="bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white shadow-md hover:shadow-lg transition-all">
                应用配置
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {config.upstream_services.map((service, index) => (
        <Card key={index} className="shadow-md hover:shadow-lg transition-all duration-200 border-gray-200 overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-white to-gray-50 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <CardTitle className="flex items-center gap-3">
                  <span className="text-lg font-semibold text-gray-800">{service.name}</span>
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-700 border border-blue-200">
                      P{service.priority}
                    </span>
                    {service.service_type && (
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        service.service_type === 'google' 
                          ? 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border border-green-200'
                          : service.service_type === 'anthropic'
                          ? 'bg-gradient-to-r from-orange-100 to-amber-100 text-orange-700 border border-orange-200'
                          : 'bg-gradient-to-r from-purple-100 to-pink-100 text-purple-700 border border-purple-200'
                      }`}>
                        {service.service_type === 'google' ? 'Google' : service.service_type === 'anthropic' ? 'Anthropic' : 'OpenAI'}
                      </span>
                    )}
                    {(!service.api_key || service.api_key.trim() === '') && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-50 text-yellow-700 border border-yellow-200">
                        ⚠️ 未配置密钥
                      </span>
                    )}
                    {service.models.length === 0 && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600 border border-gray-300">
                        📝 未配置模型
                      </span>
                    )}
                  </div>
                </CardTitle>
                <CardDescription className="text-gray-600 mt-1">
                  {service.description || '点击展开配置详情'}
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleExpand(index)}
                  className="hover:bg-gray-100 transition-colors"
                >
                  {expandedServices.has(index) ? (
                    <ChevronUp className="w-5 h-5 text-gray-600" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-600" />
                  )}
                </Button>
                {config.upstream_services.length > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeService(index)}
                    className="hover:bg-red-50 hover:text-red-600 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>

          {expandedServices.has(index) && (
            <CardContent className="space-y-4 p-6 bg-gray-50/30">
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
                  <Label className="font-medium text-gray-700">服务类型</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 transition-colors"
                    value={service.service_type || 'openai'}
                    onChange={(e) => updateService(index, 'service_type', e.target.value)}
                  >
                    <option value="openai">OpenAI</option>
                    <option value="google">Google</option>
                    <option value="anthropic">Anthropic</option>
                  </select>
                  <p className="text-sm text-gray-500">
                    服务提供商类型（OpenAI 格式兼容）
                  </p>
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
                    数字越大优先级越高（推荐：主渠道 100，备用渠道 50）
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
        </>
      )}

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
                <li><strong>优先级</strong>：数字越大优先级越高（100 比 50 优先级高）</li>
                <li><strong>自动故障转移</strong>：当高优先级渠道返回 429（限流）或 5xx 错误时，自动切换到下一优先级渠道</li>
                <li><strong>同模型多渠道</strong>：可以为同一个模型配置多个服务（如 gpt-4 配置多个 OpenAI 代理）</li>
                <li><strong>流式请求</strong>：始终使用最高优先级渠道（因为流式响应无法中途切换）</li>
                <li><strong>客户端错误</strong>：400/401/403 等客户端错误不会触发故障转移</li>
                <li><strong>占位符配置</strong>：可以保存空 API Key 或空模型列表的服务，系统会自动跳过，方便提前规划配置</li>
                <li><strong>JSON 编辑</strong>：可切换到 JSON 模式快速批量编辑所有渠道配置</li>
              </ul>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium mb-2 text-blue-900">配置示例</h4>
              <pre className="text-xs text-blue-800 overflow-x-auto">
{`upstream_services:
  - name: "openai-primary"
    priority: 100  # 主渠道（优先级最高）
    models: ["gpt-4", "gpt-4o"]
  
  - name: "openai-backup"
    priority: 50   # 备用渠道（优先级较低）
    models: ["gpt-4", "gpt-4o"]`}
              </pre>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

